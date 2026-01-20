from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from src.infrastructure.telegram.bot import get_ptb_application
from src.infrastructure.db.session import get_session
from src.services.chat_service import process_telegram_message

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Handle incoming Telegram updates via Webhook.
    """
    ptb_app = await get_ptb_application()

    # Retrieve JSON data
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Decode update
    update = Update.de_json(data, ptb_app.bot)

    # If it's a message, we might want to process it via our service manually
    # OR let PTB handle it.
    # Architecture choice:
    # Option A: Let PTB handle routing. We define handlers in bot.py that call services.
    # Option B: We intercept here and call service directly.
    #
    # Given the previous code used PTB handlers, sticking to PTB is safer for consistency.
    # We just feed the update to PTB.

    await ptb_app.update_queue.put(update)

    return {"status": "ok"}
