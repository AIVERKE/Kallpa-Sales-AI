import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.core.config import settings
from src.infrastructure.db.session import get_session
from src.services.chat_service import process_telegram_message

# Global variable to hold the application instance
_ptb_application = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy Kallpa Sales AI v2. ¿En qué puedo ayudarte?"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text

    # We need a DB session. Since PTB handlers aren't FastAPI endpoints,
    # we must create the session manually.
    async for session in get_session():
        response_text = await process_telegram_message(
            db=session,
            telegram_user_id=user_id,
            user_name=user_name,
            text=text
        )

        # Check for special flags
        if "[QR_CODE_REQUEST]" in response_text:
            clean_text = response_text.replace("[QR_CODE_REQUEST]", "").strip()
            if clean_text:
                await update.message.reply_text(clean_text)

            # Send QR Image (Assuming image.png exists in root)
            try:
                await update.message.reply_photo(photo=open("image.png", "rb"))
            except Exception as e:
                await update.message.reply_text("[No se pudo cargar el código QR]")
                print(f"Error loading QR: {e}")
        else:
            await update.message.reply_text(response_text)

        # We only need one session, so break after usage
        break

def build_application() -> Application:
    """
    Builds the Telegram Application with handlers.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        print("WARNING: No TELEGRAM_BOT_TOKEN set. Bot will not work.")

    builder = Application.builder().token(settings.TELEGRAM_BOT_TOKEN)
    app = builder.build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return app

async def get_ptb_application() -> Application:
    global _ptb_application
    if _ptb_application is None:
        _ptb_application = build_application()
        # Initialize the app (required for v20+)
        await _ptb_application.initialize()
    return _ptb_application

async def start_telegram_app():
    """
    Called by FastAPI startup event.
    """
    app = await get_ptb_application()
    await app.start()
    # In webhook mode, we don't call run_polling or updater.start_polling
    # We just ensure the app is "started" so it can process updates from queue.

async def stop_telegram_app():
    """
    Called by FastAPI shutdown event.
    """
    if _ptb_application:
        await _ptb_application.stop()
        await _ptb_application.shutdown()
