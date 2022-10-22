import datetime
import json

import requests
from SimpleQIWI import *

from tgbot import config
from tgbot.utils.dp_api import datab

API_ACCESS_TOKEN = config.QIWI_TOKEN
MY_LOGIN = config.QIWI_NUMBER

database = datab.PaymentDb()
db = datab.Sqlite()


def qiwi_check(comment):  # функция, с которой происходит вся работа. Первый аргумент - комментарий, второй - сумма
    check_time = db.last_check(comment)
    if check_time is True:
        s = requests.Session()
        s.headers['authorization'] = 'Bearer ' + API_ACCESS_TOKEN
        today = datetime.datetime.now().strftime("%Y-%m-%dT") + "00:00:00.000"
        time_now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        parameters = {'rows': '10', 'operation': 'IN',
                      'startDate': f"{today}+07:00",
                      'endDate': f"{time_now}+07:00"}
        h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + MY_LOGIN + '/payments', params=parameters)
        payments = json.loads(h.text)
        try:
            for i in range(len(payments)):
                if payments['data'][i]["comment"] == str(comment):
                    if database.check_payment(payments['data'][i]["txnId"]):
                        if payments['data'][i]["status"] == "SUCCESS":
                            return True, payments['data'][i]["sum"]["amount"]
        except IndexError:
            return False
    else:
        return check_time


def withdraw(purse, amount):
    api = QApi(token=config.QIWI_TOKEN, phone=config.QIWI_NUMBER)
    try:
        api.pay(account=purse, amount=amount, comment="Congrats")
        return True
    except Errors.QIWIAPIError:
        return False


def check_balance(api=QApi(token=config.QIWI_TOKEN, phone=config.QIWI_NUMBER)):
    return api.balance[0]
