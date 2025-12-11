from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from src.services.ai_service import ai_response
from src.database.repositories import save_ai_interaction, save_memory, get_memory

# Ruta local del QR en tu proyecto (assumes running from project root)
QR_IMAGE_PATH = "image.png"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Holaaa caserito! Soy Kallpa Sales AI 🤖. ¿Qué buscas papito?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_input = update.message.text
    user_id = update.message.from_user.id

    # 1. Obtener respuesta del modelo
    response = ai_response(user_id, user_input)

    # 2. Guardar interacción
    save_ai_interaction(
        user_id=user_id,
        customer_id=None,
        prompt=user_input,
        response=response
    )

    # 3. DETECCIÓN DE QR — antes de limpiar nada
    memory = get_memory(user_id)

    # Si ya se envió QR → NUNCA reenviarlo
    if memory and isinstance(memory, dict) and memory.get("estado_embudo") == "qr_enviado":
        clean_response = response.split("<qr>")[0].strip()
        if clean_response:
            await update.message.reply_text(clean_response)
        return

    # Si el modelo pide enviar QR
    if "<qr>" in response:
        # Enviar QR
        try:
            await update.message.reply_photo(open(QR_IMAGE_PATH, "rb"))
        except FileNotFoundError:
            await update.message.reply_text("[Error interno: No se encontró la imagen del QR]")
            print(f"Error: {QR_IMAGE_PATH} not found.")

        # Guardar estado en memoria
        save_memory(user_id, "estado_embudo", "qr_enviado")

        # Enviar mensaje sin la etiqueta
        clean_response = response.split("<qr>")[0].strip()
        if clean_response:
            await update.message.reply_text(clean_response)
        return

    # 4. Guardar último mensaje del usuario
    save_memory(user_id, "last_message", user_input)

    # 5. Responder al usuario
    await update.message.reply_text(response)


def create_bot_polling(token):
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot de Kallpa Sales AI corriendo en modo POLLING...")
    app.run_polling()

def create_telegram_bot(token):
    # This function was used in app.py for creating the bot interface (not polling)
    # But python-telegram-bot v20+ changed how this works significantly (async).
    # The original app.py was doing: `telegram_bot = create_telegram_bot(TELEGRAM_BOT_TOKEN)`
    # And then `telegram_bot.update_queue.put(data)`
    # I need to see what the original create_telegram_bot code was.
    # Wait, the original `bot.py` I viewed in Step 21 DID NOT HAVE `create_telegram_bot`.
    # It only had `create_bot_polling`.
    # BUT `app.py` line 2 IMPORTED `from telegram_bot.bot import create_telegram_bot`.
    # AND `app.py` line 7 CALLED IT.
    
    # CRITICAL: I must have missed viewing the full file or `create_telegram_bot` was implicit/imported? 
    # Let me re-read Step 21 output carefully.
    # Step 21 shows lines 1-78. `create_bot_polling` is there.
    # `create_telegram_bot` is NOT visible in Step 21 output.
    # Maybe the file was longer than 78 lines? The specific `view_file` call didn't specify lines, so it showed "entire file".
    # Wait, Step 21 says "Total Lines: 78".
    # So `app.py` was importing `create_telegram_bot` but `bot.py` didn't have it? That would cause an error.
    # OR maybe `app.py` was relying on an older version or I am misinterpreting.
    # Let's check `app.py` content again.
    # Step 13: `from telegram_bot.bot import create_telegram_bot`
    # Step 21 (bot.py) DOES NOT have `create_telegram_bot`.
    # This means the current code on disk might be BROKEN or I missed something subtle.
    # Ah, `run_bot.py` imports `create_bot_polling`.
    # `app.py` imports `create_telegram_bot`.
    
    # If `bot.py` really doesn't have it, `app.py` would fail.
    # Maybe `create_telegram_bot` is just an alias or I missed it in a previous turn?
    # No, I see "Total Lines: 78" and I see all lines.
    # This is strange.
    
    # I will assume `app.py` needs to support webhook.
    # PTB v20+ uses `Application`.
    # To support webhook in Flask, we need an `Application` instance and push updates to it.
    
    # I will implement a `create_bot_application(token)` function that returns the app,
    # and we can use it in Flask.
    pass

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return app
