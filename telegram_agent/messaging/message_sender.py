

from telegram.ext import ContextTypes

async def send_message(chat_id: int, msg: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sends an outbound Telegram message to a specific chat ID.
    """
    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown"  # Optional: allows formatting like *bold* or `code`
    )