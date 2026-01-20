from fastapi import FastAPI
from src.core.config import settings
from src.infrastructure.web.routers import webhook
from src.infrastructure.telegram.bot import start_telegram_app, stop_telegram_app
from contextlib import asynccontextmanager

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

app.include_router(webhook.router)

@app.get("/")
def home():
    return {"message": "Kallpa Sales AI is running", "version": settings.VERSION}
