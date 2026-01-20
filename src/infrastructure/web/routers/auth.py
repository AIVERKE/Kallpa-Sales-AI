from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Resolve paths
# Current file: src/infrastructure/web/routers/auth.py
# Target: src/web/templates
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # up to src/
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    # TODO: Implement real auth with DB
    # For now, hardcoded dummy check for Phase 1 testing
    if username == "admin" and password == "kallpa123":
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session", value="fake-session-token", httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error_message": "Usuario o contraseña incorrectos"
        })

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")
    return response
