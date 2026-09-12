from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from telegram_agent.message_handler.generate_response import generate_response
from telegram_agent.messaging.message_sender import send_message
from source.commands.handle_commands import handle_commands
from source.config.config import TELEGRAM_WEB_APP_URL
from source.database.user_repository import is_user_registered


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        print(f"Message from {chat_id}: {text}")

        # Show typing status while waiting for LLM
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        is_registered = await is_user_registered(user_id)
        ai_response = await generate_response(
            prompt=text,
            is_registered=is_registered,
        )
        result = await handle_commands(
            action=ai_response.action,
            telegram_user_id=user_id,
            reply=ai_response.reply,
        )
        
        if result.action == "OPEN_ONBOARDING" and TELEGRAM_WEB_APP_URL:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Set up my business", web_app=WebAppInfo(TELEGRAM_WEB_APP_URL))]]
            )
            await context.bot.send_message(chat_id=chat_id, text=result.message, reply_markup=keyboard)
        else:
            await send_message(chat_id=chat_id, msg=result.message, context=context)
