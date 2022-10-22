from aiogram import types

from tgbot import config

from tgbot.utils.dp_api import datab
payments_db = datab.PaymentDb()


def main_keyboard():
    main = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🕹Игры")
    btn2 = types.KeyboardButton("💳Баланс")
    btn3 = types.KeyboardButton(" 🛑Помощь|FAQ")
    main.add(btn1, btn2, btn3)
    return main