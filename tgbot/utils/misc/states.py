from aiogram.dispatcher.filters.state import State, StatesGroup


class States(StatesGroup):
    Create_Game = State()
    Withdraw_Qiwi_Choose = State()
    Withdraw_Amount = State()


class Admin(States):
    Mailing = State()