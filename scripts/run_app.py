import sys
import os
import argparse

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.bot.telegram_bot import create_bot_polling
from src.web.app import app

def run_web(**kwargs):
    print("Starting Flask Web App...")
    # In production, use a WSGI server like gunicorn
    if "use_reloader" not in kwargs:
         kwargs["use_reloader"] = True
    app.run(host="0.0.0.0", port=5000, debug=True, **kwargs)

def run_bot():
    print("Starting Telegram Bot (Polling)...")
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment variables.")
        return
    create_bot_polling(TELEGRAM_BOT_TOKEN)

def run_both():
    import threading
    import time
    
    # Run Flask in a separate thread
    # Must disable reloader in thread, as it requires main thread for signals
    flask_thread = threading.Thread(target=run_web, kwargs={"use_reloader": False}, daemon=True)
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(1)
    
    # Run Bot in main thread
    run_bot()

def main():
    parser = argparse.ArgumentParser(description="Kallpa Sales AI Entry Point")
    parser.add_argument("mode", choices=["web", "bot", "all"], nargs="?", help="Mode to run: web, bot, or all")
    
    args = parser.parse_args()

    # Default to 'all' if not specified
    mode = args.mode or os.getenv("RUN_MODE", "all")

    if mode == "web":
        run_web()
    elif mode == "bot":
        run_bot()
    elif mode == "all":
        run_both()
    else:
        print("Invalid mode. Use 'web', 'bot', or 'all'.")

if __name__ == "__main__":
    main()
