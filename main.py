import threading

import uvicorn
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from source.config.config import TELEGRAM_BOT_TOKEN, WEB_HOST, WEB_PORT
from telegram_agent.message_handler.handle_message import handle_message
from web_app import app as web_app


def run_web_app() -> None:
    """Run the customer chat and Telegram Web App alongside bot polling."""
    uvicorn.run(web_app, host=WEB_HOST, port=WEB_PORT)

def main() -> None:
    threading.Thread(target=run_web_app, daemon=True).start()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Pass text and photo messages (excluding commands) to the router
    app.add_handler(
        MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message)
    )

    print(f"Bot and web app are running on http://{WEB_HOST}:{WEB_PORT}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
