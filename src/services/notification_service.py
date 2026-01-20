from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import Order, Store, Notification, Customer
from src.infrastructure.telegram.bot import get_ptb_application

class NotificationService:
    @staticmethod
    async def send_sale_alert(db: AsyncSession, order_id: int):
        """
        Creates a dashboard notification and sends a Telegram message to the owner.
        """
        # 1. Fetch Data
        order = await db.get(Order, order_id)
        if not order:
            return
            
        store = await db.get(Store, order.store_id)
        customer = await db.get(Customer, order.customer_id)
        
        # 2. Create Dashboard Notification
        msg = f"Nueva Venta #{order.id}: {customer.full_name or 'Cliente'} pagó {order.total} Bs."
        notification = Notification(
            store_id=store.id,
            order_id=order.id,
            type="sale_confirmed",
            message=msg
        )
        db.add(notification)
        await db.commit()
        
        # 3. Send Telegram Alert to Owner
        if store.owner_telegram_id:
            try:
                app = await get_ptb_application()
                # Assuming bot is instance of Application, and bot.bot is the actual bot interface
                telegram_msg = (
                    f"💰 *¡NUEVA VENTA CONFIRMADA!*\n\n"
                    f"🔢 Pedido: #{order.id}\n"
                    f"👤 Cliente: {customer.full_name}\n"
                    f"💵 Monto: {order.total} Bs.\n"
                    f"✅ Estado: PAGADO (Verificado por IA)"
                )
                await app.bot.send_message(
                    chat_id=store.owner_telegram_id, 
                    text=telegram_msg,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending telegram alert to owner: {e}")
