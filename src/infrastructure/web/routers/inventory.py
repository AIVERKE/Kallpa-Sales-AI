from fastapi import APIRouter, Request, Depends, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from pathlib import Path

from src.infrastructure.db.session import get_session
from src.domain.models import Product, ProductVariant

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/inventory", response_class=HTMLResponse)
async def list_inventory(
    request: Request,
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Fetch Products with Variants
    stmt = select(Product).options(
        selectinload(Product.variants)
    ).order_by(Product.id)
    
    result = await db.execute(stmt)
    products = result.scalars().all()

    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "products": products,
        "user": {"full_name": "Administrador"}
    })

@router.post("/inventory/update-stock")
async def update_stock(
    variant_id: int = Form(...),
    new_stock: int = Form(...),
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Fetch variant
    stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
    result = await db.execute(stmt)
    variant = result.scalar_one_or_none()

    if variant:
        variant.stock_quantity = new_stock
        await db.commit()
    
    return RedirectResponse(url="/inventory", status_code=303)

@router.post("/inventory/toggle-product")
async def toggle_product(
    product_id: int = Form(...),
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Fetch product
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product:
        # Toggle simple 'active' status if logic existed, 
        # or just update a status field.
        new_status = "inactive" if product.status == "active" else "active"
        product.status = new_status
        await db.commit()
    
    return RedirectResponse(url="/inventory", status_code=303)
