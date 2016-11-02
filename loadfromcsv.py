from Application import Weibnag
from Expection import LoginFail
import csv
import sqlite3
import json
import random

FULL2HALF = dict((i + 0xFEE0, i) for i in range(0x21, 0x7F))
FULL2HALF[0x3000] = 0x20


def half_width(s):
    return str(s).translate(FULL2HALF)


def init_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "Account" (
    `username` VARCHAR(20) NOT NULL ,
    `password` VARCHAR(20) NOT NULL ,
    `young_token` VARCHAR(20)  DEFAULT '' ,
    `expire` INT  DEFAULT '0' ,
    `posts` INT  DEFAULT '0'  ,
    `replys` INT  DEFAULT '0'
    )
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
                x.bind_user_area()
                # cursor.execute("INSERT INTO 'Account' VALUES ({},{},{},0,0,0)".format(x.username, x.password, x.young_token))
                # conn.commit()
            except LoginFail:
                print(row)
                print('\033[1;31;40mError:', name, phone, pwd)
                print("\033[0m")
        print('All Done')


def rand(data):
    return data[random.randint(0, len(data) - 1)]


def post_question_with_json():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username,password,young_token,name FROM Account ")
    tokens = cursor.fetchall()

    print(tokens)
    with open('questions.json', encoding='utf-8') as q:
        data = json.load(q)
        for que in data:
            print(que)
            title = que["question"]
            content = que["answer"]

            chosen = rand(tokens)
            print(chosen)
            tmp = Weibnag(chosen[0], chosen[1])
            tmp.young_token = chosen[2]
            tmp.young_voice_url = "http://sns.qnzs.youth.cn/?token=" + chosen[2]
            tmp.post_question(title, content)

    cursor.close()
    conn.close()


if __name__ == '__main__':
    post_question_with_json()
