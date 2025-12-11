from flask import Flask, request, render_template
from telegram import Update
import asyncio
from src.bot.telegram_bot import create_telegram_bot
from src.config.settings import TELEGRAM_BOT_TOKEN, SQLALCHEMY_DATABASE_URI, SECRET_KEY
from src.web.extensions import db, login_manager
from src.web.routes.auth import auth_bp
from src.web.models import User

app = Flask(__name__)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Create tables on startup (only for dev/first run convenience)
with app.app_context():
    db.create_all()

# Initialize bot application
# Note: In a production ASGI environment, lifecycle management is different.
# For simple Flask dev server, we initialize it here.
telegram_app = create_telegram_bot(TELEGRAM_BOT_TOKEN)

# Helper to run async code in sync Flask
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route("/", methods=["GET"])
def home():
    return render_template('index.html')

from flask_login import login_required

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/webhook", methods=["POST"])
def webhook():
    # Retrieve JSON data
    data = request.get_json(force=True)
    
    # Decode update
    update = Update.de_json(data, telegram_app.bot)
    
    # Process update
    # We need to initialize the app if not already initialized
    # Ideally this should be done on startup (before first request)
    # But checking here is safer for simple scripts
    if not telegram_app._initialized:
        run_async(telegram_app.initialize())

    run_async(telegram_app.process_update(update))
    
    return "OK"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
