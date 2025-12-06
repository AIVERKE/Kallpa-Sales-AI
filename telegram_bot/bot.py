from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from openai_client.ai import ai_response
from db.queries import save_ai_interaction, save_memory, get_memory

# Ruta local del QR en tu proyecto
QR_IMAGE_PATH = "image.png"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Holaaa caserito! Soy Kallpa Sales AI 🤖. ¿Qué buscas ahicito?"
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
        await update.message.reply_photo(open(QR_IMAGE_PATH, "rb"))

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

    print("🤖 Bot de Kallpa Sales AI corriendo en modo POLLING...")
    app.run_polling()
