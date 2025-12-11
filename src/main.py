import sys
import os
import argparse

# Add project root to sys.path to ensure absolute imports work if run from inside src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.bot.telegram_bot import create_bot_polling
from src.web.app import app

def run_web():
    print("🚀 Starting Flask Web App...")
    app.run(host="0.0.0.0", port=5000, debug=True)

def run_bot():
    print("🤖 Starting Telegram Bot (Polling)...")
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment variables.")
        return
    create_bot_polling(TELEGRAM_BOT_TOKEN)

def main():
    parser = argparse.ArgumentParser(description="Kallpa Sales AI Entry Point")
    parser.add_argument("mode", choices=["web", "bot"], nargs="?", help="Mode to run: web or bot")
    
    args = parser.parse_args()

    # Default to bot if not specified, or use env var
    mode = args.mode or os.getenv("RUN_MODE", "bot")

    if mode == "web":
        run_web()
    elif mode == "bot":
        run_bot()
    else:
        print("Invalid mode. Use 'web' or 'bot'.")

if __name__ == "__main__":
    main()
