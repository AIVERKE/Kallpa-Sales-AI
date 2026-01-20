from fastapi import APIRouter, Request, Depends, Cookie, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from decimal import Decimal

from src.infrastructure.db.session import get_session
from src.domain.models import DeliveryZone, Store

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/settings/delivery", response_class=HTMLResponse)
async def settings_delivery(
    request: Request, 
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")

    # Get zones
    result = await db.execute(select(DeliveryZone).where(DeliveryZone.store_id == 1)) # Hardcoded store 1 for Phase 1
    zones = result.scalars().all()

    return templates.TemplateResponse("settings_delivery.html", {
        "request": request,
        "zones": zones,
        "user": {"full_name": "Administrador"}
    })

@router.post("/settings/delivery/add")
async def add_zone(
    name: str = Form(...),
    price: Decimal = Form(...),
    time: str = Form(None),
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")
        
    new_zone = DeliveryZone(
        store_id=1,
        name=name,
        price=price,
        estimated_time=time,
        is_active=True
    )
    db.add(new_zone)
    await db.commit()
    
    return RedirectResponse(url="/settings/delivery", status_code=303)

@router.post("/settings/delivery/delete/{zone_id}")
async def delete_zone(
    zone_id: int,
    session: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    if not session:
        return RedirectResponse(url="/login")
        
    zone = await db.get(DeliveryZone, zone_id)
    if zone:
        await db.delete(zone)
        await db.commit()
        
    return RedirectResponse(url="/settings/delivery", status_code=303)
