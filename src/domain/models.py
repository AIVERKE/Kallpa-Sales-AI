from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, BigInteger, JSON, Enum, func, DateTime
import enum

# Enums
class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    store_owner = "store_owner"
    sales_agent = "sales_agent"

class OrderStatus(str, enum.Enum):
    draft = "draft"
    pending_payment = "pending_payment"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    returned = "returned"

class PaymentMethod(str, enum.Enum):
    qr_transfer = "qr_transfer"
    cash_on_delivery = "cash_on_delivery"
    card_link = "card_link"

# 1. TIENDAS
class Store(SQLModel, table=True):
    __tablename__ = "stores"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    name: str = Field(sa_column=Column(String(200), nullable=False))
    slug: str = Field(sa_column=Column(String(100), unique=True, nullable=False))
    bot_token: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    currency: str = Field(default="BOB", sa_column=Column(String(3)))
    qr_image_url: Optional[str] = Field(default=None, sa_column=Column(Text))
    owner_telegram_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    settings: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    users: List["User"] = Relationship(back_populates="store")
    products: List["Product"] = Relationship(back_populates="store")
    customers: List["Customer"] = Relationship(back_populates="store")

# 2. USUARIOS
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: Optional[int] = Field(default=None, foreign_key="stores.id")
    name: str = Field(sa_column=Column(String(150), nullable=False))
    email: str = Field(sa_column=Column(String(150), unique=True, nullable=False))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    role: UserRole = Field(default=UserRole.store_owner)
    phone: Optional[str] = Field(default=None, sa_column=Column(String(20)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    store: Optional[Store] = Relationship(back_populates="users")

# 3. ZONAS DE DELIVERY
class DeliveryZone(SQLModel, table=True):
    __tablename__ = "delivery_zones"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    name: str = Field(sa_column=Column(String(100), nullable=False))
    price: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2)))
    estimated_time: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    is_active: bool = Field(default=True)

# 4. PRODUCTOS
class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    name: str = Field(sa_column=Column(String(200), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    base_price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    category: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    status: str = Field(default="active", sa_column=Column(String(20)))
    image_url: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    store: Store = Relationship(back_populates="products")
    variants: List["ProductVariant"] = Relationship(back_populates="product")

# 5. VARIANTES DE PRODUCTO
class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    product_id: int = Field(foreign_key="products.id")
    sku: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    size: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    color: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    additional_price: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2)))
    stock_quantity: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

    product: Product = Relationship(back_populates="variants")

# 6. USUARIOS DE TELEGRAM
class TelegramIdentity(SQLModel, table=True):
    __tablename__ = "telegram_identities"
    telegram_id: int = Field(sa_column=Column(BigInteger, primary_key=True))
    first_name: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    username: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    language_code: Optional[str] = Field(default=None, sa_column=Column(String(10)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

# 7. CLIENTES
class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    telegram_id: Optional[int] = Field(default=None, foreign_key="telegram_identities.telegram_id")

    phone: Optional[str] = Field(default=None, sa_column=Column(String(30)))
    email: Optional[str] = Field(default=None, sa_column=Column(String(150)))
    full_name: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    address: Optional[str] = Field(default=None, sa_column=Column(Text))

    ltv: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2)))
    status: str = Field(default="lead", sa_column=Column(String(20)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

    store: Store = Relationship(back_populates="customers")
    telegram_identity: Optional[TelegramIdentity] = Relationship()
    orders: List["Order"] = Relationship(back_populates="customer")

# 8. SESIONES DE CHAT
class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    customer_id: int = Field(foreign_key="customers.id")

    current_flow: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    current_step: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    context_data: Optional[dict] = Field(default={}, sa_column=Column(JSON))

    last_interaction_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    is_active: bool = Field(default=True)

# 9. PEDIDOS
class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    customer_id: int = Field(foreign_key="customers.id")

    status: OrderStatus = Field(default=OrderStatus.draft)
    payment_method: Optional[PaymentMethod] = Field(default=None)

    subtotal: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2), nullable=False))
    delivery_cost: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2)))
    total: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2), nullable=False))

    delivery_zone_id: Optional[int] = Field(default=None, foreign_key="delivery_zones.id")
    shipping_address: Optional[str] = Field(default=None, sa_column=Column(Text))

    payment_proof_url: Optional[str] = Field(default=None, sa_column=Column(Text))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    items: List["OrderItem"] = Relationship(back_populates="order")
    customer: Customer = Relationship(back_populates="orders")

# 10. DETALLE DEL PEDIDO
class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    order_id: int = Field(foreign_key="orders.id")
    product_variant_id: Optional[int] = Field(default=None, foreign_key="product_variants.id")

    product_name: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    variant_name: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    quantity: int = Field(nullable=False)
    unit_price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    total_line: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    order: Order = Relationship(back_populates="items")

# 11. INTERACCIONES AI
class AiLog(SQLModel, table=True):
    __tablename__ = "ai_logs"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: Optional[int] = Field(default=None, foreign_key="stores.id")
    chat_session_id: Optional[int] = Field(default=None, foreign_key="chat_sessions.id")
    input_tokens: Optional[int] = Field(default=None)
    output_tokens: Optional[int] = Field(default=None)
    model_used: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    user_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    ai_response: Optional[str] = Field(default=None, sa_column=Column(Text))
    sentiment_score: Optional[float] = Field(default=None, sa_column=Column(Numeric(3, 2)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

# 12. NOTIFICACIONES (Dashboard/System)
class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    store_id: int = Field(foreign_key="stores.id")
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id")
    
    type: str = Field(sa_column=Column(String(50))) # sale, alert, stock_low
    message: str = Field(sa_column=Column(Text))
    is_read: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
