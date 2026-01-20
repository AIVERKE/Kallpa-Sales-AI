from fastapi import APIRouter, Request, Depends, Cookie, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from pathlib import Path

from src.infrastructure.db.session import get_session
from src.domain.models import Order, OrderStatus, Customer, OrderItem

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/orders", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    status: str = "all",
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Build Query
    stmt = select(Order).options(
        selectinload(Order.customer).selectinload(Customer.telegram_identity),
        selectinload(Order.items)
    ).order_by(desc(Order.created_at))

    if status != "all":
        # Map simple status to Enum if needed, or rely on string match
        stmt = stmt.where(Order.status == status)

    result = await db.execute(stmt)
    orders = result.scalars().all()

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": orders,
        "current_status": status,
        "user": {"full_name": "Administrador"}
    })

@router.post("/orders/{order_id}/update-status")
async def update_order_status(
    order_id: int,
    new_status: str = Form(...),
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Fetch order
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if order:
        order.status = new_status
        await db.commit()
    
    # Redirect back to where we came from (referer) or default to order list
    return RedirectResponse(url="/orders", status_code=303)
