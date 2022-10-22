import logging

from aiogram import Dispatcher
# import telebot
import aiogram

from tgbot.config import ADMINS_ID, TOKEN

from tgbot.utils import qiwi_api

# bot = telebot.TeleBot(TOKEN)
bot = aiogram.Bot(TOKEN)


async def on_startup_notify(dp: Dispatcher):
    for admin in ADMINS_ID:
        try:
            await dp.bot.send_message(admin, "Бот Запущен")

        except Exception as err:
            logging.exception(err)


def send_result_to_creator(result, creator_id, game_id, amount, numb, username):
    if result:
        bot.send_message(chat_id=creator_id, text=f"🏁Игра №{game_id} окончена\n"
                                                  f"Поздравляю, вы победили!\n\n"
                                                  f"Противник: @{username}\n"
                                                  f"Выпавшее число: {numb}\n"
                                                  f"Сумма ставки: {amount}\n")
    else:
        bot.send_message(chat_id=creator_id, text=f"🏁Игра №{game_id} окончена\n"
                                                  f"К сожалению, вы проиграли(\n\n"
                                                  f"Противник: {username}"
                                                  f"Выпавшее число: {numb}\n"
                                                  f"Сумма ставки: {amount}\n")


def send_payment_info(amount, user):
    bot.send_message(chat_id="-1001178054212", text=f"Баланс пользователя @{user} был пополнен на {amount} руб\n"
                                                    f"Баланс кошелька бота: {qiwi_api.qiwi.check_balance()}")


def send_withdraw_info(amount, user):
    bot.send_message(chat_id="-1001178054212", text=f"Новая заявка на вывод от @{user} на {amount - amount / 10} руб\n"
                                                    f"Баланс кошелька бота: {qiwi_api.qiwi.check_balance()} руб")
