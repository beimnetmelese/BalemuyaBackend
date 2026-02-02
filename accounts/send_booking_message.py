import os
import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv

def send_booking_message(telegram_id, message, button_text, button_url):
    load_dotenv()
    API_TOKEN = os.getenv("BOT_API_KEY")
    bot = Bot(token=API_TOKEN)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, web_app=WebAppInfo(url=button_url))]
    ])
    bot.send_message(chat_id=telegram_id, text=message, reply_markup=keyboard)
