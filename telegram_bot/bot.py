from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai_client.ai import ai_response
from db.queries import save_ai_interaction


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy Kallpa Sales AI 🤖. ¿En qué puedo ayudarte hoy?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.message.from_user.id

    # Llamada a DeepSeek
    response = ai_response(user_input)

    # Guardar en BD
    save_ai_interaction(
        user_id=user_id,
        customer_id=None,
        prompt=user_input,
        response=response
    )

    # Responder al usuario
    await update.message.reply_text(response)


def create_bot_polling(token):
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot de Kallpa Sales AI corriendo en modo POLLING...")
    app.run_polling()
