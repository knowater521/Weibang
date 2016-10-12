from Application import Weibnag
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
            print('Doing:',name)
            try:
                x = Weibnag(half_width(phone),half_width(pwd))
                x.reg()
            except:
                print('Error:',name,phone,pwd)
                pass
        print('All Done')


if __name__ == '__main__':
    main()

