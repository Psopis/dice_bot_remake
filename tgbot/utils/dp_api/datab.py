import sqlite3
# import utils
import time


class Sqlite:
    def __init__(self):
        with sqlite3.connect("../../database.db") as conn:
            self.conn = conn
            self.cur = self.conn.cursor()

    def user_exist(self, user_id):
        query = f"select id from users where id = {user_id}"
        res = self.cur.execute(query).fetchone()
        if not res:
            query = f"insert into users(id, balance, last_check) values ({user_id}, 0, 0)"
            self.cur.execute(query)
            self.conn.commit()

    def get_users_id(self):
        query = f"select id from users"
        res = self.cur.execute(query).fetchall()
        return res

    def gen_games(self):
        query = f"select amount, game_id from games_now"
        res = self.cur.execute(query).fetchall()
        return res

    def check_play(self, user_id, game_id):
        query = f"select id_of_creator, username from games_now where game_id = {game_id}"
        res = self.cur.execute(query).fetchone()
        if res[0] == user_id:
            return False
        return res[1]

    def check_balance(self, user_id, game_id=None, flag=True):
        query = f"select balance from users where id = {user_id}"
        balance = self.cur.execute(query).fetchone()[0]
        if flag:
            query = f"select amount from games_now where game_id = {game_id}"
            amount = self.cur.execute(query).fetchone()[0]
            if balance < amount:
                return False
            return True
        else:
            return balance

    def kill_game(self, game_id, player_id, won, numb, username):
        query = f"select id_of_creator, amount from games_now where game_id = {game_id}"
        res = self.cur.execute(query).fetchone()
        query = f"delete from games_now where game_id = {game_id}"
        self.cur.execute(query)
        if won:
            winner_id = player_id
            sign = "+"
            result = False
        else:
            winner_id = res[0]
            sign = "-"
            result = True
        utils.send_result_to_creator(result, res[0], game_id, res[1], numb, username)
        query = f"insert into previous_games(id_of_creator, second_player_id, winner, game_id, numb, amount) values({res[0]}, {player_id}, {winner_id}, {game_id}, {numb}, {res[1]})"
        self.cur.execute(query)
        query = f"update users set balance = balance {sign} {res[1]} where id = {player_id}"
        self.cur.execute(query)
        if result:
            query = f"update users set balance = balance + {res[1] * 2} where id = {res[0]}"
            self.cur.execute(query)
        self.conn.commit()
        return res[1]

    def create_new_game(self, user_id, sum_of_game, username):
        if self.check_balance(user_id=user_id, flag=False) >= sum_of_game:
            query = f"select count(*) from games_now where id_of_creator = {user_id}"
            res = self.cur.execute(query).fetchone()
            if res[0] < 3:
                query = f"insert into games_now(id_of_creator, amount, username) values({user_id}, {sum_of_game}, '{username}')"
                self.cur.execute(query)
                query = f"update users set balance = balance - {sum_of_game} where id = {user_id}"
                self.cur.execute(query)
                self.conn.commit()
                return "0"
            else:
                return "1"
        else:
            return "2"

    def give_stats(self, user_id):
        query = f"select winner, amount from previous_games where id_of_creator = {user_id} or second_player_id = {user_id}"
        result = self.cur.execute(query).fetchall()
        games = len(result)
        wins = 0
        loses = 0
        money_won = 0
        money_lost = 0
        for elem in result:
            if elem[0] == user_id:
                wins += 1
                money_won += elem[1]
            else:
                loses += 1
                money_lost += elem[1]
        profit = money_won - money_lost
        try:
            middle_sum = (money_won + money_lost) / games
        except ZeroDivisionError:
            middle_sum = 0
        return games, wins, loses, money_won, money_lost, profit, middle_sum

    def update_balance(self, user_id, amount, sign):
        query = f"update users set balance = balance {sign} {amount} where id = {user_id}"
        self.cur.execute(query)
        self.conn.commit()

    def last_check(self, user_id):
        query = f"select last_check from users where id = {user_id}"
        res = self.cur.execute(query).fetchone()
        if (res[0] - time.time()) > 0:
            return res[0] - time.time()
        else:
            query = f"update users set last_check = {time.time() + 30} where id = {user_id}"
            self.cur.execute(query)
            self.conn.commit()
            return True


class PaymentDb:  # Класс базы данных, не трогать
    def __init__(self):
        self.conn = sqlite3.connect("../../payments.db", check_same_thread=False)
        self.cur = self.conn.cursor()

    def check_payment(self, txnId):
        query = f"select txnId from payments where txnId = {txnId}"
        res = self.cur.execute(query).fetchone()
        if not res:
            self.insert_txnid(txnId)
            return True

    def gen_all_withdraws(self):
        query = f"select purce, sum, id from withdraw_requests"
        res = self.cur.execute(query).fetchall()
        return res

    def insert_txnid(self, txnId):
        query = f"insert into payments(txnId) values ('{txnId}')"
        self.cur.execute(query)
        self.conn.commit()

    def new_withdraw_request(self, purce, sum):
        query = f"insert into withdraw_requests(purce, sum) values ({purce}, {sum})"
        self.cur.execute(query)
        self.conn.commit()

    def delete_withdraw(self, id):
        query = f"delete from withdraw_requests where id = {id}"
        self.cur.execute(query)
        self.conn.commit()
