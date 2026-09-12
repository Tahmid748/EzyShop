from telegram import Update
from telegram.ext import ContextTypes

from telegram_agent.message_handler.generate_response import generate_response
from telegram_agent.messaging.message_sender import send_message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        chat_id = update.effective_chat.id
        
        print(f"Message from {chat_id}: {text}")

        # Show typing status while waiting for LLM
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        response = await generate_response(prompt=text)
        
        # Await the async send_message helper with chat_id and context
        await send_message(chat_id=chat_id, msg=response, context=context)