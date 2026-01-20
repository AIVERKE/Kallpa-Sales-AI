from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import TelegramIdentity, Customer, ChatSession, Store, AiLog
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

    # 4. Call LLM Service
    raw_response = await get_ai_response(text, customer, session)

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

    return final_text
