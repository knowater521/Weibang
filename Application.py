import hashlib
import requests
import json
import time
from websocket import create_connection


def crypt(data, key):
    """RC4 algorithm"""
    x = 0
    box = list(range(256))
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

    return ''.join(out)


class Weibnag:
    username = ''
    password = ''
    uid = ''
    token = ''
    s = requests.session()

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        username_encrypt = crypt(self.username, 'h8uJk2U8ew9H17ycbN6gH0c8Lmn6Ko2p')
        passwd__encrypt = hashlib.sha1(self.password.encode()).hexdigest()

        data = {
            "httphost": "123.103.5.54",
            "httpport": "9456",
            "username": username_encrypt,
            "password": passwd__encrypt,
            "device_token": "",
            "socketType": "websocketio",
            "version": ""
        }

        self.s.post('http://weibang.youth.cn/public/web/service/webmanager/dispatchByWebBrowser',
                    data={'host': 'weibang.youth.cn', 'port': '80', 'username': raw_username})
        userinfo = self.s.post("http://weibang.youth.cn/public/web/service/webmanager/login_safe", data=data).json()

        userinfo = json.loads(userinfo)
        self.uid = userinfo['data']['uid']
        self.token = userinfo['data']['access_token']

    def websocket(self):
        socket_detail = requests.get('http://123.103.5.50:9056/socket.io/1/?t=%d' % time.time() * 1000).text
        wsurl = 'ws://123.103.5.50:9056/socket.io/1/websocket/' + socket_detail.split(':')[0]
        ws = create_connection(wsurl)
        ws.send(
            '''3:::{"id":2,"route":"connector.entryHandler.connect","msg":{"uid":"%s","username":"%s","token":"%s","version":"","sockettype":"websocketio","device_type":"4","device_token":"","unit_type":"web"}}''' % (
                uid, raw_username, token))
        print(ws.recv())
        ws.send(
            """3:::{"id":3,"route":"api.systemHandler.getUserDetail","msg":{"my_uid":"%s","user_detail_sync_tag":"","token":"%s"}}""" % (
                self.uid, self.token))
        print(ws.recv())
        ws.send("""3:::{"id":4,"route":"api.orgHandler.get_org_list","msg":{"my_uid":"%s","opt_uid":"%s","token":"%s"}}
        """ % (self.uid, self.uid, self.token))
        ws.send("""3:::{"id":5,"route":"api.systemHandler.getUserDetail","msg":{"my_uid":"%s","user_detail_sync_tag":"","token":"%s"}}
        """ % (self.uid, self.token))
        ws.send("""3:::{"id":6,"route":"api.systemHandler.getBrandNewConversation","msg":{"my_uid":"%s","opt_uid":"%s","token":"%s"}}
        """ % (self.uid, self.uid, self.token))
        ws.send(
            """3:::{"id":7,"route":"api.orgHandler.get_org_list","msg":{"my_uid":"%s","opt_uid":"%s","token":"%s"}}""" % (
                self.uid, self.uid, self.token))
        print(ws.recv())
        print(ws.recv())
        print(ws.recv())

    def extra_req(self):
        self.s.get('http://weibang.youth.cn/public/web/service/webmanager/getSiteType')

    def reg(self):
        self.login()
        self.websocket()
        self.extra_req()


if __name__ == "__main__":
    pass
