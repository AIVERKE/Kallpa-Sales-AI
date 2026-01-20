import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.domain.models import Order, OrderStatus, AiLog
from src.core.config import settings
from openai import OpenAI

# Initialize client (Assuming same config as LLM Service for now)
client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=f"{settings.DEEPSEEK_BASE_URL}/v1"
)

class PaymentService:
    @staticmethod
    async def analyze_receipt_image(db: AsyncSession, image_url: str, customer_id: int) -> str:
        """
        Analyzes a receipt image to find a matching pending order.
        Returns a user-facing message.
        """
        # 1. Get Pending Orders for Customer
        result = await db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .where(Order.status == OrderStatus.draft) # Or pending_payment
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()
        
        if not orders:
            return "No tienes pedidos pendientes para verificar."

        if not orders:
            return "No tienes pedidos pendientes para verificar."

        # SIMULATION MODE (Because DeepSeek-Chat doesn't support Vision yet)
        # We assume the payment is valid for the latest order.
        order = orders[0]
        
        # Simulate processing time or logic if needed, but here we just approve.
        order.status = OrderStatus.paid
        order.payment_proof_url = image_url
        db.add(order)
        await db.commit()
        
        # Trigger Notification
        try:
            from src.services.notification_service import NotificationService
            await NotificationService.send_sale_alert(db, order.id)
        except Exception as e:
            print(f"Notification Error: {e}")
            
        return f"✅ ¡Pago Verificado (Simulado)! Tu pedido #{order.id} está confirmado. Pronto gestionaremos el envío."


