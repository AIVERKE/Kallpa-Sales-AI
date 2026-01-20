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
        if "[QR_DYNAMIC:" in response_text:
            # Extract URL
            import re
            match = re.search(r"\[QR_DYNAMIC:(.*?)\]", response_text)
            if match:
                qr_url = match.group(1)
                clean_text = response_text.replace(match.group(0), "").strip()
                
                if clean_text:
                    await update.message.reply_text(clean_text)
                
                try:
                    # In production, this would download the URL or use a File ID.
                    # For local dev, if it's a file path, open it. 
                    # If it interprets as external URL, Telegram might need 'send_photo(url)'
                    # We assume it's a URL or path accessible server-side.
                    await update.message.reply_photo(photo=qr_url)
                except Exception as e:
                    await update.message.reply_text("[No se pudo cargar la imagen del QR]")
                    print(f"Error loading QR {qr_url}: {e}")
            else:
                await update.message.reply_text(response_text)
                
        elif "[QR_CODE_REQUEST]" in response_text:
             # Fallback for legacy static QR
            clean_text = response_text.replace("[QR_CODE_REQUEST]", "").strip()
            if clean_text:
                await update.message.reply_text(clean_text)

            try:
                await update.message.reply_photo(photo=open("image.png", "rb"))
            except Exception as e:
                pass
        else:
            await update.message.reply_text(response_text)

        # We only need one session, so break after usage
        break

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async for session in get_session():
        from src.services.chat_service import reset_chat_session
        response = await reset_chat_session(session, user_id)
        await update.message.reply_text(response)
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
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    return app

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Get highest resolution photo
    photo_file = await update.message.photo[-1].get_file()
    
    # Telegram File URL (Requires standard API URL construction if not provided by library directly usually)
    # PTB provides file_path but it needs token insertion usually or we let GPT download it if public.
    # Actually PTB Download is protected. We might need to download it to a buffer or rely on PTB's 'file_path' if the LLM client can access it (Unlikely without auth).
    # Ideally: Download -> Upload to LLM or passing Base64.
    # For now, we assume we pass the URL provided by Telegram (which expires).
    # Simplified: We will say "Recibido" if we can't fully pipe the URL without a public server.
    # BUT, let's try to get the link.
    
    file_url = photo_file.file_path
    
    async for session in get_session():
        from src.services.chat_service import process_receipt
        response_text = await process_receipt(session, user_id, file_url)
        await update.message.reply_text(response_text)
        break

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
