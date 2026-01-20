from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.core.config import settings
from src.infrastructure.web.routers import webhook, auth, dashboard, orders, inventory, customers
from src.infrastructure.web.routers import settings as settings_router
from src.infrastructure.telegram.bot import start_telegram_app, stop_telegram_app
from contextlib import asynccontextmanager
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Telegram App...")
    await start_telegram_app()
    yield
    # Shutdown
    print("Stopping Telegram App...")
    await stop_telegram_app()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Mount Static Files
# src/web/static
BASE_DIR = Path(__file__).resolve().parent.parent.parent # src
STATIC_DIR = BASE_DIR / "web" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(webhook.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(customers.router)
app.include_router(settings_router.router)

@app.get("/")
def home():
    return RedirectResponse(url="/login")
