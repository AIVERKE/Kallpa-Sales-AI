import sys
import os
import argparse

# Add project root to sys.path to ensure absolute imports work if run from inside src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from src.core.config import settings
from src.infrastructure.telegram.bot import build_application
from src.infrastructure.web.main import app

def run_web():
    print("🚀 Starting FastAPI Web App...")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

def run_bot():
    print("🤖 Starting Telegram Bot (Polling)...")
    if not settings.TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        return
    
    app_bot = build_application()
    print("✅ Bot is running! Press Ctrl+C to stop.")
    app_bot.run_polling()

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
