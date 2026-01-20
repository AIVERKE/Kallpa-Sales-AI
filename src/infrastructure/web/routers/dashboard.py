from fastapi import APIRouter, Request, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, cast, String
from datetime import datetime, date, timezone
from pathlib import Path

from src.infrastructure.db.session import get_session
from src.domain.models import Order, OrderStatus, ProductVariant, Notification

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(
    request: Request, 
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    # Simple auth check
    if not session:
        return RedirectResponse(url="/login")

    # 1. METRICS: Sales Today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query: Total paid today
    # Fix: Cast ENUM to String to avoid asyncpg type cache compilation errors
    query_sales = select(func.sum(Order.total)).where(
        Order.created_at >= today_start,
        cast(Order.status, String) == "paid"
    )
    result_sales = await db.execute(query_sales)
    sales_today = result_sales.scalar() or 0

    # 2. METRICS: Pending Orders (To Ship)
    query_pending = select(func.count(Order.id)).where(
        cast(Order.status, String) == "paid" # Paid but not shipped yet
    )
    result_pending = await db.execute(query_pending)
    pending_orders = result_pending.scalar() or 0

    # 3. METRICS: Low Stock Alerts (< 5 units)
    query_stock = select(func.count(ProductVariant.id)).where(ProductVariant.stock_quantity < 5)
    result_stock = await db.execute(query_stock)
    low_stock_count = result_stock.scalar() or 0

    # 4. RECENT NOTIFICATIONS / FEED
    query_notifs = select(Notification).order_by(Notification.created_at.desc()).limit(10)
    result_notifs = await db.execute(query_notifs)
    notifications = result_notifs.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": {
            "sales_today": sales_today,
            "pending_orders": pending_orders,
            "low_stock": low_stock_count
        },
        "notifications": notifications,
        "user": {"full_name": "Administrador"} # Placeholder for logged user
    })
