import os
import telebot

API_TOKEN = os.getenv("BOT_API_KEY")
bot = telebot.TeleBot(API_TOKEN)

def send_booking_message(telegram_id, message, button_text, button_url):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text=button_text, url=button_url))
    bot.send_message(chat_id=telegram_id, text=message, reply_markup=keyboard)
