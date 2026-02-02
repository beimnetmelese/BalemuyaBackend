import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

API_TOKEN = os.getenv("BOT_API_KEY")
bot = Bot(token=API_TOKEN)

async def send_booking_message(telegram_id, message, button_text, button_url):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, web_app=WebAppInfo(url=button_url))]
    ])
    await bot.send_message(chat_id=telegram_id, text=message, reply_markup=keyboard)

# telegram_helpers.py
import asyncio
from threading import Thread
from .send_booking_message import send_booking_message

def send_booking_message_sync(*args, **kwargs):
    """
    Runs the async send_booking_message in a background thread,
    so you can call it like a normal synchronous function.
    """
    def runner():
        asyncio.run(send_booking_message(*args, **kwargs))
    
    Thread(target=runner).start()
