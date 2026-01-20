from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import TelegramIdentity, Customer, ChatSession, Store, AiLog, Order
from src.services.llm_service import get_ai_response, parse_memory_tags, clean_response

async def process_telegram_message(
    db: AsyncSession,
    telegram_user_id: int,
    user_name: str,
    text: str,
    store_id: int = 1 # Default store for single-tenant bot, or derived from context
) -> str:

    # 1. Get or Create Telegram Identity
    result = await db.execute(select(TelegramIdentity).where(TelegramIdentity.telegram_id == telegram_user_id))
    identity = result.scalars().first()

    if not identity:
        identity = TelegramIdentity(
            telegram_id=telegram_user_id,
            first_name=user_name
        )
        db.add(identity)
        await db.commit()
        await db.refresh(identity)

    # 2. Get or Create Customer for this Store
    result = await db.execute(
        select(Customer)
        .where(Customer.telegram_id == telegram_user_id)
        .where(Customer.store_id == store_id)
    )
    customer = result.scalars().first()

    if not customer:
        customer = Customer(
            store_id=store_id,
            telegram_id=telegram_user_id,
            full_name=user_name,
            status="lead"
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    # 3. Get or Create Active Chat Session
    # Logic: If last interaction was > 24h, create new session?
    # For now, just get the last active one.
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.customer_id == customer.id)
        .where(ChatSession.is_active == True)
        .order_by(ChatSession.last_interaction_at.desc())
    )
    session = result.scalars().first()

    if not session:
        session = ChatSession(
            store_id=store_id,
            customer_id=customer.id,
            current_flow="GENERAL"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # 4a. Get Chat History (Last 6 messages)
    history_logs = await db.execute(
        select(AiLog)
        .where(AiLog.chat_session_id == session.id)
        .order_by(AiLog.created_at.desc())
        .limit(6)
    )
    logs = history_logs.scalars().all()
    # Reorder to chronological (oldest -> newest)
    logs = reversed(logs)
    
    history_messages = []
    for log in logs:
        # User message
        history_messages.append({"role": "user", "content": log.user_message})
        # AI response (clean only to avoid re-injecting tags logic? OR raw? 
        # Typically we want clean text for context, but maybe raw for logic continuity. 
        # Let's use clean text to avoid confusing the LLM with old tags)
        
        # Actually, for continuity, raw might be better if we want it to remember it made an order.
        # But 'clean_response' removes system tags, which is safer visual context.
        # Let's use raw_response but handle the output carefully.
        # Ideally, we store "clean_response" in DB too.
        # Let's use the stored ai_response for now.
        history_messages.append({"role": "assistant", "content": log.ai_response})

    # 4b. Search Products & Zones
    from src.services.product_service import ProductService
    from src.services.delivery_service import DeliveryService
    
    products_found = await ProductService.search_products_by_text(db, text, store_id)
    product_context = ProductService.format_products_for_llm(products_found)
    
    available_zones = await DeliveryService.get_available_zones(db, store_id)
    delivery_context = DeliveryService.format_zones_for_llm(available_zones)

    # 5. Call LLM Service
    raw_response = await get_ai_response(text, customer, session, product_context, delivery_context, history=history_messages)

    # 5. Process Tags (<memoria>)
    memory_update = parse_memory_tags(raw_response)
    if memory_update:
        # Update Customer or Session Context
        # Example: Update fields in Customer if they match
        for key, value in memory_update.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
            else:
                # Add to session context if not a customer field
                current_context = dict(session.context_data) if session.context_data else {}
                current_context[key] = value
                session.context_data = current_context

        db.add(customer)
        db.add(session)

    # 6. Log Interaction
    log = AiLog(
        store_id=store_id,
        chat_session_id=session.id,
        user_message=text,
        ai_response=raw_response,
        model_used="deepseek-chat" # Should come from settings or response
    )
    db.add(log)

    await db.commit()

    # 7. Return Clean Response
    final_text = clean_response(raw_response)

    # Handle <qr> if needed (return a flag or handle here?)
    # For simplicity, if <qr> is in raw_response, the Bot Adapter will handle it
    # by checking the raw string if we return it, OR we return a complex object.
    # Here we just return text for now, but in a real app we might return a struct.

    if "<qr>" in raw_response:
        final_text += " [QR_CODE_REQUEST]"

    # 6. Process Order Creation Tag
    if "<crear_pedido>" in raw_response:
        try:
            import json
            from src.services.order_service import OrderService
            
            # Extract JSON
            json_str = raw_response.split("<crear_pedido>")[1].split("</crear_pedido>")[0]
            items_raw = json.loads(json_str)
            
            # Resolve SKUs from Attributes if needed
            items_data = []
            for item in items_raw:
                sku = item.get("sku")
                qty = item.get("cantidad", 1)
                
                # Check if we have attributes to fallback
                if "product_name" in item:
                    # Try to resolve valid SKU via attributes
                    variant = await ProductService.find_best_match_variant(
                         db, 
                         store_id, 
                         item["product_name"], 
                         item.get("color"), 
                         item.get("size")
                    )
                    if variant:
                        sku = variant.sku # Override hallucinated SKU with real one
                
                items_data.append({"sku": sku, "cantidad": qty})
            
            # Create Order
            try:
                order = await OrderService.create_order(db, store_id, customer.id, items_data)
                
                # Success Message Injection
                final_text += f"\n\n✅ ¡Pedido #{order.id} creado con éxito!\nTotal a Pagar: {order.total} Bs."
                
                # Fetch Store QR to display
                store = await db.get(Store, store_id)
                if store and store.qr_image_url:
                    final_text += f"\n\nEscanea el QR para pagar:\n[QR_DYNAMIC:{store.qr_image_url}]"
                else:
                    final_text += "\n\n(Solicita el QR de pago al vendedor)"
                
            except ValueError as ve:
                # Stock error or invalid SKU
                final_text += f"\n\n⚠️ No pudimos procesar tu pedido: {str(ve)}"
                
        except Exception as e:
            print(f"Error creating order: {e}")
            final_text += "\n\n(Error técnico al generar el pedido, por favor intenta de nuevo)"

    # 7. Process Zone Assignment Tag
    if "<asignar_zona>" in raw_response:
        try:
            zone_id_str = raw_response.split("<asignar_zona>")[1].split("</asignar_zona>")[0]
            zone_id = int(zone_id_str)
            
            # Use most recent active order for this customer
            # Ideally, we should track 'current_order_id' in session context.
            # For this prototype, we fetch the last PENDING/DRAFT order.
            
            result = await db.execute(
                select(Order)
                .where(Order.customer_id == customer.id)
                .where(Order.status == "draft")
                .order_by(Order.created_at.desc())
            )
            current_order = result.scalars().first()
            
            if current_order:
                updated_order = await OrderService.update_shipping(db, current_order.id, zone_id)
                 # Success Message Injection
                final_text += f"\n\n🚚 Envío actualizado. Nuevo Total: {updated_order.total} Bs."
            else:
                final_text += "\n\n⚠️ No encontré un pedido activo para asignarle envío."

        except Exception as e:
            print(f"Error assigning zone: {e}")
            final_text += "\n\n(Error al calcular envío)"

    return final_text

async def process_receipt(
    db: AsyncSession,
    telegram_user_id: int,
    file_url: str,
    store_id: int = 1
) -> str:
    """
    Processes a receipt image sent by a user.
    """
    # Find Customer
    result = await db.execute(
        select(Customer)
        .where(Customer.telegram_id == telegram_user_id)
        .where(Customer.store_id == store_id)
    )
    customer = result.scalars().first()
    
    if not customer:
        return "No estás registrado en nuestra base de datos."

    from src.services.payment_service import PaymentService
    response_text = await PaymentService.analyze_receipt_image(db, file_url, customer.id)
    
    return response_text

async def reset_chat_session(
    db: AsyncSession,
    telegram_user_id: int,
    store_id: int = 1
) -> str:
    """
    Deactivates current session to clear context history.
    """
    # Find Customer
    result = await db.execute(
        select(Customer)
        .where(Customer.telegram_id == telegram_user_id)
        .where(Customer.store_id == store_id)
    )
    customer = result.scalars().first()
    
    if not customer:
        return "No tienes una sesión activa para reiniciar."

    # Deactivate all active sessions
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.customer_id == customer.id)
        .where(ChatSession.is_active == True)
    )
    sessions = result.scalars().all()
    
    for session in sessions:
        session.is_active = False
        db.add(session)
        
    await db.commit()
    return "🔄 Sesión reiniciada. He olvidado nuestra conversación anterior. ¿En qué puedo ayudarte ahora?"

