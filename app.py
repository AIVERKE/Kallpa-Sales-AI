from flask import Flask, request
from telegram_bot.bot import create_telegram_bot
from config import TELEGRAM_BOT_TOKEN

app = Flask(__name__)

telegram_bot = create_telegram_bot(TELEGRAM_BOT_TOKEN)

@app.route("/", methods=["GET"])
def home():
    return "Kallpa Sales AI Chatbot OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    telegram_bot.update_queue.put(data)
    return "OK"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
