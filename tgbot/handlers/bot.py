import asyncio

from aiogram import Bot, types
from aiogram.types import CallbackQuery
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.builtin import Command
from aiogram.utils import executor
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from tgbot import config
# import utils
from tgbot.utils import telebot_part
from tgbot.utils.misc.states import States, Admin
from tgbot import keyboards
from tgbot.utils.dp_api import datab
from tgbot.utils.qiwi_api import qiwi

bot = Bot(config.TOKEN)
memory_storage = MemoryStorage()
dp = Dispatcher(bot, storage=memory_storage)

database = datab.Sqlite()
pays = datab.PaymentDb()

Admin_Keyboards = keyboards.inline.AdminPanel()


@dp.message_handler(Command("start"))
async def start(message: types.message):  # Ответ на комманду /start
    await bot.send_message(message.chat.id,
                           "Добро пожаловать в лучшее казино",
                           reply_markup=keyboards.reply.main_keyboard())
    database.user_exist(message.chat.id)


@dp.message_handler(Command("admin"))
async def join_into_a_panel(message: types.message):  # Вход в админ панель
    if message.chat.id in config.ADMINS_ID:
        await bot.send_message(chat_id=message.chat.id,
                               text="Добро пожаловать в админ панель!",
                               reply_markup=Admin_Keyboards.in_admin_panel())


@dp.callback_query_handler(text="qiwibalance")
async def send_qiwi_balance(call: CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id, text=f"{qiwi.check_balance()} рублей")
    await call.answer()


@dp.callback_query_handler(text="admin_withdraw")
async def choose_withdraw(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Все заявки на вывод",
                                reply_markup=Admin_Keyboards.gen_all_withdraws())
    await call.answer()


@dp.callback_query_handler(text_contains="withdrawaccept")
async def give_withdraw_info(call: CallbackQuery):
    data = call.data.split(":")
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f"Номер кошелька: {data[1]}\n"
                                     f"Сумма на вывод: {data[2]}\n"
                                     f"Баланс кошелька: {qiwi.check_balance()}",
                                reply_markup=Admin_Keyboards.withdraw_info(data[1], data[2], data[3]))
    await call.answer()


@dp.callback_query_handler(text_contains="okwithdraw")
async def withdraw(call: CallbackQuery):
    await call.answer()
    data = call.data.split(":")
    if qiwi.withdraw(data[1], data[2]):
        await call.answer(text="Вывод вроде осуществлен, но на самом деле я хз", show_alert=True)
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text="Добро пожаловать в админ панель!",
                                    reply_markup=Admin_Keyboards.in_admin_panel())
        pays.delete_withdraw(data[3])
    else:
        await call.answer(text="Теньге нема, сук", show_alert=True)
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text="Добро пожаловать в админ панель!",
                                    reply_markup=Admin_Keyboards.in_admin_panel())


@dp.callback_query_handler(text_contains="delete")
async def delete_withdraw(call: CallbackQuery):
    data = call.data.split(":")
    await call.answer(text="Заявка удалена", show_alert=True)
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Добро пожаловать в админ панель!",
                                reply_markup=Admin_Keyboards.in_admin_panel())
    pays.delete_withdraw(data[1])


@dp.callback_query_handler(text="mailing")
async def confirm_mail(call: CallbackQuery):
    await Admin.Mailing.set()
    await call.answer()
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="Назад", callback_data="backadminpanel")
    markup.add(btn)
    await bot.send_message(call.message.chat.id,
                           "Напишите текст для рассылки или отправьте картиначку",
                           reply_markup=markup)


@dp.callback_query_handler(text="play")
async def play_button(call: CallbackQuery):  # Отображает список игр
    await bot.edit_message_text(text="🎭 Созданные игры:",
                                message_id=call.message.message_id,
                                chat_id=call.message.chat.id,
                                reply_markup=keyboards.inline.games_markup(database.gen_games()))
    await call.answer()


@dp.callback_query_handler(text_contains="game")
async def choose_game(call: CallbackQuery):  # Выбор какой-либо игры
    game_id = call.data.split(":")
    res = database.check_play(call.message.chat.id, game_id[1])
    if res:
        await bot.edit_message_text(text=f"Игра номер: {game_id[1]}\n"
                                         f"Сумма: {game_id[2]}\n"
                                         f"Создатель игры: @{res}\n"
                                         f"\nВнимание! Действие броска отменить нельзя",
                                    message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    reply_markup=keyboards.inline.accept_game_markup(game_id[1]))
    else:
        await bot.edit_message_text(text=f"Игра номер: {game_id[1]}\n"
                                         f"Сумма: {game_id[2]}\n"
                                         f"\nЭто ваша игра. Ожидаем соперника!",
                                    message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    reply_markup=keyboards.inline.accept_game_markup(game_id[1], flag=False))
    await call.answer()


@dp.callback_query_handler(text_contains="accept")
async def trow_dice(call: CallbackQuery):  # Бросок кости
    game_id = call.data.split(":")[1]
    if database.check_balance(call.message.chat.id, game_id):
        res = await bot.send_dice(call.message.chat.id, reply_markup=keyboards.inline.remove_keyboard())
        await asyncio.sleep(3.5)
        if res.dice.value <= 3:
            won = False
            await call.answer(text="К сожалению, вы проиграли(", show_alert=True)
        else:
            won = True
            await call.answer(text="Вы выиграли!!!", show_alert=True)
        amount = database.kill_game(game_id, call.message.chat.id, won, res.dice.value, call.message.chat.username)
        if won:
            await bot.send_message(call.message.chat.id,
                                   f"🏁Игра №{game_id} окончена!\n"
                                   f"Выпавшее число: {res.dice.value}\n"
                                   f"Сумма игры: {amount} руб\n"
                                   f"--------------------------\n"
                                   f"🏆Вы победили!!!\n"
                                   f"🧾Ваш выигрыш: {amount * 2}")
        else:
            await bot.send_message(call.message.chat.id,
                                   f"Игра №{game_id} окончена!\n"
                                   f"Выпавшее число: {res.dice.value}\n"
                                   f"Сумма игры: {amount} руб\n"
                                   f"--------------------------\n"
                                   f"Вы проиграли(")
    else:
        await call.answer(show_alert=True, text="У вас недостаточно денег на счету(")
        await bot.edit_message_text(text="Список игр",
                                    message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    reply_markup=keyboards.inline.games_markup(database.gen_games()))


@dp.callback_query_handler(text="create")
async def new_game(call: CallbackQuery):  # Создание новой игры
    await States.Create_Game.set()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f"Введите сумму вашей ставки\n"
                                     f"Ваш баланс: "
                                     f"{database.check_balance(user_id=call.message.chat.id, flag=False)}",
                                reply_markup=keyboards.inline.back_button())
    await call.answer()


@dp.callback_query_handler(text="stats")
async def give_stats(call: CallbackQuery):
    stats = database.give_stats(call.message.chat.id)
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f"Статистика ваших игр:\n"
                                     f"🎲Всего игр: {stats[0]}\n"
                                     f"🏆Побед: {stats[1]}\n"
                                     f"🥴Поражений: {stats[2]}\n"
                                     f"➖➖➖➖➖➖➖➖➖➖➖\n"
                                     f"Финансы \n"
                                     f"🏆Выиграно: {stats[3]} руб\n"
                                     f"🗑 Проиграно: {stats[4]} руб\n\n"
                                     f"📉Средняя ставка: {int(stats[6])}\n"
                                     f"🧾Профит: {stats[5]} руб",
                                reply_markup=keyboards.inline.back_button(flag=True))
    await call.answer()


@dp.callback_query_handler(text="pay")
async def choose_payment_method(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Выберите, через какую платежную систему вы хотите пополнить баланс",
                                reply_markup=keyboards.inline.choose_payments())
    await call.answer()


@dp.callback_query_handler(text="withdraw")
async def withdraw_check(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Выберите платежную систему",
                                reply_markup=keyboards.inline.choose_withdraw())
    await call.answer()


@dp.callback_query_handler(text="qiwi_api")
async def qiwi_pay_menu(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f'''Информация об оплате
🥝 QIWI-кошелек: {config.QIWI_NUMBER}
📝 Комментарий к переводу: {call.message.chat.id}
➖➖➖➖➖➖➖➖➖➖

Пополните указанный киви кошелёк на любую сумму.
Перевод должен быть совершён с киви кошелька.
Обязательно в рублях.

⛔️ При пополнении БЕЗ комментария
Манибэка НЕ последует.
Не тратьте ни своё, ни наше время.

При нажатии оплатить в браузере, вам останется ввести лишь сумму платежа.''',
                                reply_markup=keyboards.inline.qiwi_payment(call.message.chat.id))
    await call.answer()


@dp.callback_query_handler(text="check_pay")
async def check_qiwi_pay(call: CallbackQuery):
    res = qiwi.qiwi_check(call.message.chat.id)
    if type(res) == tuple:
        await call.answer(text=f"Вы успешно пополнили баланс на {res[1]} руб!", show_alert=True)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        database.update_balance(user_id=call.message.chat.id, amount=res[1], sign="+")
        telebot_part.send_payment_info(res[1], call.message.chat.username)
    elif res:
        await call.answer(text=f"Подождите еще {round(res)} сек, чтобы заново проверить оплату")
    else:
        await call.answer(text=f"Оплата не найдена")


@dp.callback_query_handler(text="qiwi_withdraw")
async def choose_qiwi(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Напишите номер киви кошелька(без +) для вывода")
    await call.answer()
    await States.Withdraw_Qiwi_Choose.set()


@dp.callback_query_handler(text="withdraw_all", state=States.Withdraw_Amount)
async def withdraw_all(call: CallbackQuery, state: FSMContext):
    balance = database.check_balance(flag=False, user_id=call.message.chat.id)
    if balance > 0:
        data = await state.get_data()
        purse = data.get("purse")
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=f"Коммисия: 10%\n"
                                         f"Сумма к выводу: {balance - balance / 10}\n"
                                         f"Кошелек для вывода: {purse}\n\n"
                                         f"Вывод происходит в полуавтоматическом режиме.\n"
                                         f"Деньги придут в течение 24 часов.\n\n"
                                         f"❗️Проверьте правильность и подтвердите вывод.",
                                    reply_markup=keyboards.inline.agree_to_withdraw(balance, purse))
        await state.finish()
    else:
        await call.answer(text="К сожалению, на вашем счету недостаточно денег")
        await bot.delete_message(chat_id=call.message.chat.id,
                                 message_id=call.message.message_id)
        await state.finish()


@dp.callback_query_handler(text_contains="agree")
async def agree_to_withdraw(call: CallbackQuery):  # Составление заявки на вывод
    data = call.data.split(":")
    purse = data[1]
    amount = int(data[2])
    telebot_part.send_withdraw_info(amount, call.message.chat.username)
    await call.answer(text="Заявка на вывод успешно создана!")
    pays.new_withdraw_request(purse, amount - amount / 10)
    database.update_balance(call.message.chat.id, amount, "-")
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@dp.callback_query_handler(text="back")
async def back_button(call: CallbackQuery):  # Кнопка назад, возвращающая в главное меню
    await bot.edit_message_text(text='''🎮 Создайте свою игру или вступите в игру соперника:
1. После создания игры ожидайте соперника!
2. Соперник, принявший игру, кидает кубик 🎲
3. Выпавшая цифра больше 3.5 победа за вами!
4. Выпавшая цифра меньше 3.5 победа соперника!
🎯 Погнали?''',
                                message_id=call.message.message_id,
                                chat_id=call.message.chat.id,
                                reply_markup=keyboards.inline.game_or_stats_markup())
    await call.answer()


@dp.callback_query_handler(text="back1")
async def cancel_game(call: CallbackQuery):  # Кнопка назад, возвращающая в список всех игр
    await bot.edit_message_text(text="🎭 Созданные игры:",
                                message_id=call.message.message_id,
                                chat_id=call.message.chat.id,
                                reply_markup=keyboards.inline.games_markup(database.gen_games()))
    await call.answer()


@dp.callback_query_handler(text="back2", state=States.Create_Game)
async def cancel_create_game(call: CallbackQuery, state: FSMContext):  # Кнопка назад, возвращающая в список всех игр
    await bot.edit_message_text(text=" Созданные игры:",
                                message_id=call.message.message_id,
                                chat_id=call.message.chat.id,
                                reply_markup=keyboards.inline.games_markup(database.gen_games()))
    await call.answer()
    await state.finish()
    await call.answer()


@dp.callback_query_handler(text="back3", state="*")
async def cancel_pay(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f"Ваш баланс: {database.check_balance(flag=False, user_id=call.message.chat.id)}",
                                reply_markup=keyboards.inline.pay_or_withdraw())
    await call.answer()


@dp.callback_query_handler(text="back4")
async def cancel_qiwi_pay(call: CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Выберите, через какую платежную систему вы хотите пополнить баланс",
                                reply_markup=keyboards.inline.choose_payments())
    await call.answer()


@dp.callback_query_handler(text="backadminpanel", state="*")
async def back_to_admin_panel(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Добро пожаловать в админ панель!",
                                reply_markup=Admin_Keyboards.in_admin_panel())
    await call.answer()


@dp.message_handler(state=Admin.Mailing)
async def mailing(message: types.message, state: FSMContext):
    lst = database.get_users_id()
    msg = await bot.send_message(chat_id=-1001209512088, text=message.text)
    for elem in lst:
        try:
            await bot.forward_message(chat_id=elem[0],
                                      from_chat_id=-1001209512088,
                                      message_id=msg.message_id)
        except Exception as e:
            print(e)
    await state.finish()
    await bot.send_message(message.chat.id,
                           "Рассылка завершена. Возврат в главное меню",
                           reply_markup=Admin_Keyboards.in_admin_panel())


@dp.message_handler(content_types=["photo"], state=Admin.Mailing)
async def mailing(message: types.message, state: FSMContext):
    lst = database.get_users_id()
    msg = await bot.send_photo(chat_id=-1001209512088, photo=message.photo[0].file_id, caption=message.caption)
    for elem in lst:
        try:
            await bot.forward_message(chat_id=elem[0],
                                      from_chat_id=-1001209512088,
                                      message_id=msg.message_id)
        except Exception as e:
            print(e)
    await state.finish()
    await bot.send_message(message.chat.id,
                           "Рассылка завершена. Возврат в главное меню",
                           reply_markup=Admin_Keyboards.in_admin_panel())


@dp.message_handler()
async def main(message: types.message):  # Обработчик всех сообщений
    if message.text == "🕹Игры":
        await bot.send_message(message.chat.id,
                               '''🎮 Создайте свою игру или вступите в игру соперника:
1. После создания игры ожидайте соперника!
2. Соперник, принявший игру, кидает кубик 🎲
3. Выпавшая цифра больше 3.5 - победа за вами!
4. Выпавшая цифра меньше 3.5 - победа соперника!
🎯 Погнали?!''',
                               reply_markup=keyboards.inline.game_or_stats_markup())
    elif message.text == "💳Баланс":
        await bot.send_message(message.chat.id,
                               f"🏷Ваш баланс: {database.check_balance(flag=False, user_id=message.chat.id)}",
                               reply_markup=keyboards.inline.pay_or_withdraw())
    elif message.text == "🛑Помощь|FAQ":
        await message.answer("https://telegra.ph/PomoshchFAQ-07-03")


@dp.message_handler(state=States.Create_Game)
async def create_game(message: types.message, state: FSMContext):  # Обработчик при создании новых игр
    try:
        numb = int(message.text)
        if numb > 0:
            result = database.create_new_game(message.chat.id, numb, message.from_user.username)
            if result == "0":
                await message.answer("Вы успешно создали игру. Теперь ожидайте соперника и получайте деньги)")
                await state.finish()
            elif result == "1":
                await bot.send_message(message.chat.id,
                                       "Вы пытаетесь создать больше трех игр одновременно!",
                                       reply_markup=keyboards.inline.back_button())
            elif result == "2":
                await bot.send_message(message.chat.id,
                                       "К сожалению, на балансе недостаточно средств",
                                       reply_markup=keyboards.inline.back_button())
        else:
            await bot.send_message(message.chat.id,
                                   "Введите правильное число!",
                                   reply_markup=keyboards.inline.back_button())
    except ValueError:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back2"))
        await bot.send_message(message.chat.id, "Введите число", reply_markup=markup)


@dp.message_handler(state=States.Withdraw_Qiwi_Choose)
async def insert_qiwi(message: types.message, state: FSMContext):
    try:
        purse = int(message.text)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"✅ Qiwi кошелек: {purse}\n"
                                    f"💵 Ваш баланс: {database.check_balance(flag=False, user_id=message.chat.id)}\n"
                                    f"Введите сумму для вывода или нажмите на кнопку",
                               reply_markup=keyboards.inline.choose_withdraw_1())
        await state.update_data(purse=purse)
        await States.Withdraw_Amount.set()
    except ValueError:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text="Отменить", callback_data="back3")
        markup.add(btn1)
        await bot.send_message(chat_id=message.chat.id,
                               text="Введите правильный кошелек!",
                               reply_markup=markup)


@dp.message_handler(state=States.Withdraw_Amount)
async def insert_amount(message: types.message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount > 1:
            if database.check_balance(user_id=message.chat.id, flag=False) >= amount:
                data = await state.get_data()
                purse = data.get("purse")
                await bot.send_message(chat_id=message.chat.id,
                                       text=f"Коммисия: 10%\n"
                                            f"Сумма к выводу: {amount - amount / 10}\n"
                                            f"Кошелек для вывода: {purse}\n\n"
                                            f"Вывод происходит в полуавтоматическом режиме.\n"
                                            f"Деньги придут в течение 24 часов.\n\n"
                                            f"❗️Проверьте правильность и подтвердите вывод.",
                                       reply_markup=keyboards.inline.agree_to_withdraw(amount, purse))
                await state.finish()
            else:
                markup = types.InlineKeyboardMarkup(row_width=1)
                btn1 = types.InlineKeyboardButton("Отменить вывод", callback_data="back3")
                markup.add(btn1)
                await bot.send_message(chat_id=message.chat.id,
                                       text="На вашем счету недостаточно денег",
                                       reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn1 = types.InlineKeyboardButton("Отменить вывод", callback_data="back3")
            markup.add(btn1)
            await bot.send_message(chat_id=message.chat.id,
                                   text="Минимальное число для вывода - 2 рубля",
                                   reply_markup=markup)
    except ValueError:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Назад", callback_data="back3")
        markup.add(btn1)
        await bot.send_message(message.chat.id,
                               "Вы ввели неправильное число. Повторите попытку",
                               reply_markup=markup)


async def on_start(dp):
    await telebot_part.on_startup_notify(dp)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, on_startup=on_start)
