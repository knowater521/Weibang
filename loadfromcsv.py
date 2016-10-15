from Application import Weibnag
from Expection import LoginFail
import csv


FULL2HALF = dict((i + 0xFEE0, i) for i in range(0x21, 0x7F))
FULL2HALF[0x3000] = 0x20


def half_width(s):
    return str(s).translate(FULL2HALF)


def main():
    with open('user.csv', newline='') as csvfile:
        data = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in data:
            name = row[1]
            phone = row[2]
            pwd = row[3]
            if not phone.isdigit():
                continue
            try:
                x = Weibnag(half_width(phone), half_width(pwd))
                x.bind_user_area()
            except LoginFail:
                print(row)
                print('\033[1;31;40mError:', name, phone, pwd)
                print("\033[0m")
        print('All Done')


if __name__ == '__main__':
    main()

