from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.domain.models import DeliveryZone

class DeliveryService:
    @staticmethod
    async def get_available_zones(db: AsyncSession, store_id: int) -> List[DeliveryZone]:
        """
        Fetches active delivery zones for the store.
        And appends a virtual 'Pickup' zone.
        """
        result = await db.execute(
            select(DeliveryZone)
            .where(DeliveryZone.store_id == store_id)
            .where(DeliveryZone.is_active == True)
        )
        zones = result.scalars().all()
        # Convert to list to append virtual zone
        zones_list = list(zones)
        
        # Virtual Zone: Recojo en Tienda
        # We use a dummy object or a dict. For type safety let's use a dummy object if possible 
        # or just handle it in the formatter. 
        # Let's create a temporary object.
        pickup_zone = DeliveryZone(
            id=-1, # Special ID
            store_id=store_id,
            name="Recojo en Tienda (Gratis)",
            price=0,
            estimated_time="Inmediato"
        )
        zones_list.append(pickup_zone)
        
        return zones_list

    @staticmethod
    def format_zones_for_llm(zones: List[DeliveryZone]) -> str:
        """
        Formats zones so the LLM knows the IDs and Prices.
        """
        if not zones:
            return "No hay zonas de delivery configuradas."
        
        lines = []
        for z in zones:
            lines.append(f"ID: {z.id} | Zona: {z.name} | Costo: {z.price} Bs. | Tiempo: {z.estimated_time or 'N/A'}")
        
        return "\n".join(lines)
