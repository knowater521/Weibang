from Application import Weibnag
from Expection import LoginFail
from tools import half_width
import csv
import sqlite3



def init_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE Account
    (
        name INTEGER,
        username TEXT,
        password TEXT,
        young_token TEXT,
        type INTEGER
    );
    """)
    conn.commit()
    cursor.close()
    conn.close()


def check_and_insert_database():
    with open('user.csv', newline='') as csvfile:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        data = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in data:
            name = row[1]
            phone = row[2]
            pwd = row[3]
            if not phone.isdigit():
                continue
            try:
                x = Weibnag(half_width(phone), half_width(pwd))
                x.login()
                x.websocket(False)
                cursor.execute("INSERT INTO 'Account' VALUES ('{}','{}','{}','{}',0)"
                               .format(name, x.username, x.password, x.young_token))
                conn.commit()
            except LoginFail:
                print(row)
                print('\033[1;31;40mError:', name, phone, pwd)
                print("\033[0m")
        print('All Done')
        conn.commit()
        cursor.close()
        conn.close()


def read_from_sql():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    lists = cursor.execute("SELECT * FROM Account").fetchall()
    print(lists)
    for each in lists:
        x = Weibnag(each[0], each[1], each[2])
        x.bind_user_area()


if __name__ == '__main__':
    pass
