from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.domain.models import Order, OrderItem, ProductVariant, OrderStatus

class OrderService:
    @staticmethod
    async def create_order(
        db: AsyncSession,
        store_id: int,
        customer_id: int,
        items_data: List[Dict[str, any]]
    ) -> Order:
        """
        Creates an order from a list of items (SKU, quantity).
        Validates stock and deducts it.
        """
        # 1. Validate Items & Stock
        order_items = []
        total_amount = 0
        
        # We process items sequentially to check stock
        # In a real high-concurrency app, we might need 'select for update' locking.
        for item in items_data:
            sku = item.get("sku")
            qty = item.get("cantidad", 1)
            
            # Find Variant
            result = await db.execute(select(ProductVariant).where(ProductVariant.sku == sku))
            variant = result.scalars().first()
            
            if not variant:
                raise ValueError(f"Producto con SKU '{sku}' no encontrado.")
            
            if variant.stock_quantity < qty:
                raise ValueError(f"Stock insuficiente para '{sku}'. Disponible: {variant.stock_quantity}")
            
            # Deduct Stock
            variant.stock_quantity -= qty
            db.add(variant)
            
            # Prepare Order Item
            # We need the product name too. Assuming variant.product is loaded or we fetch it.
            # Ideally we fetch product too. For now let's rely on relationship or simple data.
            # Variant table has price override, but we need base price from product.
            # Let's fetch product to be safe.
            product = await db.get(variant.product.__class__, variant.product_id)
            
            unit_price = product.base_price + variant.additional_price
            total_line = unit_price * qty
            
            order_item = OrderItem(
                product_variant_id=variant.id,
                product_name=product.name,
                variant_name=f"{variant.size or ''} {variant.color or ''}".strip(),
                quantity=qty,
                unit_price=unit_price,
                total_line=total_line
            )
            order_items.append(order_item)
            total_amount += total_line

        # 2. Create Order
        new_order = Order(
            store_id=store_id,
            customer_id=customer_id,
            status=OrderStatus.draft, # Starts as draft until payment/confirmation logic
            subtotal=total_amount,
            total=total_amount, # Delivery added later
            items=order_items
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        return new_order
        
    @staticmethod
    async def update_shipping(db: AsyncSession, order_id: int, zone_id: int) -> Order:
        """
        Updates the order with the selected shipping zone and recalculates total.
        """
        # Get Order
        order = await db.get(Order, order_id)
        if not order:
            raise ValueError("Pedido no encontrado")
            
        delivery_cost = 0
        zone_name = "Recojo en Tienda"
        
        if zone_id == -1:
            # Pickup
            order.delivery_zone_id = None
            order.shipping_address = "Recojo en Tienda"
        else:
            # Fetch Zone
            zone = await db.get(DeliveryZone, zone_id)
            if not zone:
                raise ValueError("Zona de delivery no válida")
            delivery_cost = zone.price
            zone_name = zone.name
            order.delivery_zone_id = zone.id
            
        # Update Totals
        order.delivery_cost = delivery_cost
        order.total = order.subtotal + delivery_cost
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        return order

