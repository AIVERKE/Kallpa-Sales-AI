from fastapi import APIRouter, Request, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc
from datetime import datetime, date, timezone
from pathlib import Path

from src.infrastructure.db.session import get_session
from src.domain.models import Customer, Order, OrderStatus

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/customers", response_class=HTMLResponse)
async def customers_list(
    request: Request, 
    filter_status: str = "all",
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Base query
    query = select(Customer)

    # Filter by Status (lead vs active customer)
    if filter_status and filter_status != "all":
        query = query.where(Customer.status == filter_status)

    # Default sort by LTV desc (Big spenders first)
    query = query.order_by(desc(Customer.ltv))
    
    result = await db.execute(query)
    customers = result.scalars().all()
    
    # Calculate some summary stats to show on top
    # We could do this with SQL count() but list len is fine for MVP
    total_leads = len(customers)

    return templates.TemplateResponse("customers.html", {
        "request": request,
        "customers": customers,
        "filter_status": filter_status,
        "user": {"full_name": "Administrador"}
    })
