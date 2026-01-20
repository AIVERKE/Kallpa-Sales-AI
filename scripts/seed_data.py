import asyncio
import sys
import os

# Adjust path to enable imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.db.session import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from src.domain.models import Store, Product, ProductVariant, DeliveryZone, User, Order, OrderItem, Customer, ChatSession, TelegramIdentity, AiLog, Notification

async def seed_data():
    # 0. Recreate Schema (Force update for development)
    print("Recreating schema...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Schema created.")

    # Create session factory manually since it's not exported
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("Seeding database...")

        # 1. Create Store
        # IMPORTANT: Replace using your own telegram ID in 'owner_telegram_id' to verify alerts!
        store = Store(
            name="Kallpa Boutique",
            slug="kallpa-boutique",
            currency="BOB",
            owner_telegram_id=123456789, # REPLACE THIS with your ID to test notifications
            qr_image_url="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=KallpaBoutiquePago" # PNG QR
        )
        db.add(store)
        await db.commit()
        await db.refresh(store)
        print(f"Store created: {store.name} (ID: {store.id})")

        # 2. Delivery Zones
        zones = [
            DeliveryZone(store_id=store.id, name="Sopocachi / Centro", price=10, estimated_time="30-45 min"),
            DeliveryZone(store_id=store.id, name="Zona Sur (Calacoto/Obrajes)", price=15, estimated_time="45-60 min"),
            DeliveryZone(store_id=store.id, name="Ciudad Satélite (El Alto)", price=20, estimated_time="1-2 horas"),
        ]
        db.add_all(zones)
        print(f"Delivery Zones created")

        # 3. Products
        p1 = Product(
            store_id=store.id, 
            name="Jean Clásico Stonewash", 
            description="Pantalón jean corte recto, tela rígida premium.",
            base_price=150
        )
        
        p2 = Product(
            store_id=store.id, 
            name="Camiseta Oversize Kallpa", 
            description="Camiseta 100% algodón pima con diseño andino minimalista.",
            base_price=80
        )
        
        db.add(p1)
        db.add(p2)
        await db.commit()
        await db.refresh(p1)
        await db.refresh(p2)

        # 4. Variants
        variants = [
            # Jean Variants
            ProductVariant(product_id=p1.id, sku="JEAN-AZ-38", size="38", color="Azul Clásico", stock_quantity=5),
            ProductVariant(product_id=p1.id, sku="JEAN-AZ-40", size="40", color="Azul Clásico", stock_quantity=3),
            ProductVariant(product_id=p1.id, sku="JEAN-NE-38", size="38", color="Negro", stock_quantity=2),
            
            # T-Shirt Variants
            ProductVariant(product_id=p2.id, sku="TSHIRT-BL-M", size="M", color="Blanco", stock_quantity=10),
            ProductVariant(product_id=p2.id, sku="TSHIRT-BL-L", size="L", color="Blanco", stock_quantity=8),
            ProductVariant(product_id=p2.id, sku="TSHIRT-NE-M", size="M", color="Negro", stock_quantity=5),
        ]
        db.add_all(variants)
        await db.commit()
        print(f"Products & Variants created")
        
        print("Database seeded successfully! Ready to test.")

if __name__ == "__main__":
    asyncio.run(seed_data())
