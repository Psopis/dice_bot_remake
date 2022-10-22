from aiogram import types

from tgbot import config

from tgbot.utils.dp_api import datab

payments_db = datab.PaymentDb()


def game_or_stats_markup():
    games_markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🎮Играть", callback_data="play")
    btn2 = types.InlineKeyboardButton("🔥Статистика", callback_data="stats")
    games_markup.add(btn1, btn2)
    return games_markup


def games_markup(list_of_games):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for elem in list_of_games:
        markup.add(types.InlineKeyboardButton(f"🎮Игра №{elem[1]}: Ставка - {elem[0]} рублей",
                                              callback_data=f"game:{elem[1]}:{elem[0]}"))
    btn1 = types.InlineKeyboardButton("💲Создать свою игру", callback_data="create")
    btn2 = types.InlineKeyboardButton("◀️Назад", callback_data="back")
    markup.add(btn1, btn2)
    return markup


def accept_game_markup(game_id, flag=True):
    lst = []
    markup = types.InlineKeyboardMarkup(row_width=1)
    if flag:
        lst.append(types.InlineKeyboardButton("Бросить кубик", callback_data=f"accept:{game_id}"))
    lst.append(types.InlineKeyboardButton("◀️Назад", callback_data="back1"))
    markup.add(*lst)
    return markup


def back_button(flag=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if flag:
        markup.add(types.InlineKeyboardButton("◀️Назад", callback_data="back"))
    else:
        markup.add(types.InlineKeyboardButton("◀️Назад", callback_data="back2"))
    return markup


def remove_keyboard():
    markup = types.InlineKeyboardMarkup()
    return markup


def pay_or_withdraw():
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton("↪️Пополнить", callback_data="pay")
    button2 = types.InlineKeyboardButton("↩️Вывести", callback_data="withdraw")
    markup.add(button1, button2)
    return markup


def choose_payments():
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("🥝qiwi_api", callback_data="qiwi_api")
    button2 = types.InlineKeyboardButton("◀️Назад", callback_data="back3")
    markup.add(button1, button2)
    return markup


def choose_withdraw():
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("🥝qiwi_api", callback_data="qiwi_withdraw")
    button2 = types.InlineKeyboardButton("◀️Назад", callback_data="back3")
    markup.add(button1, button2)
    return markup


def choose_withdraw_1():
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("Вывести все", callback_data="withdraw_all")
    button2 = types.InlineKeyboardButton("Отменить вывод", callback_data="back3")
    markup.add(button1, button2)
    return markup


def qiwi_payment(chat_id):
    url = f"https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={config.QIWI_NUMBER}&amountInteger=None&amountFraction=0&extra%5B%27comment%27%5D={chat_id}&currency=643&blocked[0]=account&blocked[2]=comment"
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text="Проверить оплату", callback_data="check_pay")
    btn2 = types.InlineKeyboardButton(text="Оплатить в браузере", url=url)
    btn3 = types.InlineKeyboardButton(text="◀️Назад", callback_data="back4")
    markup.add(btn1, btn2, btn3)
    return markup


def agree_to_withdraw(amount, purse):
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton("Подтверждаю вывод", callback_data=f"agree:{purse}:{amount}")
    button2 = types.InlineKeyboardButton("Отменить вывод", callback_data="back3")
    markup.add(button1, button2)
    return markup


class AdminPanel:
    @staticmethod
    def in_admin_panel():
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Заявки на вывод", callback_data="admin_withdraw")
        btn2 = types.InlineKeyboardButton("Рассылка", callback_data="mailing")
        btn3 = types.InlineKeyboardButton("Баланс кошелька бота", callback_data="qiwibalance")
        markup.add(btn1, btn2, btn3)
        return markup

    @staticmethod
    def gen_all_withdraws():
        res = payments_db.gen_all_withdraws()
        markup = types.InlineKeyboardMarkup(row_width=1)
        for elem in res:
            markup.add(
                types.InlineKeyboardButton(text=elem[1], callback_data=f"withdrawaccept:{elem[0]}:{elem[1]}:{elem[2]}"))
        markup.add(types.InlineKeyboardButton(text="Назад", callback_data="backadminpanel"))
        return markup

    @staticmethod
    def withdraw_info(purse, amount, id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(text="Подвердить вывод", callback_data=f"okwithdraw:{purse}:{amount}:{id}")
        btn3 = types.InlineKeyboardButton(text="Удалить запрос", callback_data=f"delete:{id}")
        btn2 = types.InlineKeyboardButton(text="Назад", callback_data="backadminpanel")
        markup.add(btn1, btn3, btn2)
        return markup
