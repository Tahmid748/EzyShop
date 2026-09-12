from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from source.config.config import TELEGRAM_BOT_TOKEN
from telegram_agent.message_handler.handle_message import handle_message

def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Pass text and photo messages (excluding commands) to the router
    app.add_handler(
        MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message)
    )

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()