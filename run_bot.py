from telegram_bot.bot import create_bot_polling
from config import TELEGRAM_BOT_TOKEN

if __name__ == "__main__":
    create_bot_polling(TELEGRAM_BOT_TOKEN)
