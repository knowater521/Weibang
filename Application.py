import hashlib
import requests
import json
import time
from websocket import create_connection
from Expection import LoginFail

debugLevel = 0


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


def log(msg, level=1, color=False):
    if level > debugLevel:
        if color:
            print("\033[1;33;40m" + msg + "\033[0m")
        else:
            print(msg)


class Weibnag:
    username = ''
    password = ''
    uid = ''
    token = ''
    young_voice_url = ''
    s = requests.session()
    young = requests.session()
    header = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/602.1.50\
                            (KHTML, like Gecko) Mobile/14A456"}
    young.headers = header
    s.headers = header
    debug = True

    def __init__(self, username, password):
        log('[INFO] user ' + username, 2, True)
        self.username = username
        self.password = password

    def login(self):
        log('[INFO] simulate login from web', 2, True)

        username_encrypt = crypt(self.username, 'h8uJk2U8ew9H17ycbN6gH0c8Lmn6Ko2p')
        passwd_encrypt = hashlib.sha1(self.password.encode()).hexdigest()

        data = {
            "httphost": "123.103.5.54",
            "httpport": "9456",
            "username": username_encrypt,
            "password": passwd_encrypt,
            "device_token": "",
            "socketType": "websocketio",
            "version": ""
        }

        self.s.post('http://weibang.youth.cn/public/web/service/webmanager/dispatchByWebBrowser',
                    data={'host': 'weibang.youth.cn', 'port': '80', 'username': self.username})
        userinfo = self.s.post("http://weibang.youth.cn/public/web/service/webmanager/login_safe", data=data).json()
        log(userinfo)
        userinfo = json.loads(userinfo)

        if userinfo['code'] != "200":
            log('[Error]' + self.username + '密码错误', 5, True)
            raise LoginFail

        self.uid = userinfo['data']['uid']
        self.token = userinfo['data']['access_token']

    def websocket(self, first_time=False):
        log('[INFO] simulate web socket', 2, True)

        socket_detail = requests.get('http://123.103.5.50:9056/socket.io/1/?t=%d' % time.time() * 1000).text
        wsurl = 'ws://123.103.5.50:9056/socket.io/1/websocket/' + socket_detail.split(':')[0]

        ws = create_connection(wsurl)
        log(ws.recv())

        ws.send(
            '''3:::{"id":2,"route":"connector.entryHandler.connect","msg":{"uid":"%s","username":"%s","token":"%s",
            "version":"","sockettype":"websocketio","device_type":"4","device_token":"","unit_type":"web"}}'''
            % (self.uid, self.username, self.token))
        log(ws.recv())

        if first_time:
            ws.send(
                """3:::{"id":3,"route":"api.systemHandler.getUserDetail","msg":{"my_uid":"%s","user_detail_sync_tag":
                "","token":"%s"}}"""
                % (self.uid, self.token))
            log(ws.recv())

            ws.send(
                """3:::{"id":4,"route":"api.orgHandler.get_org_list","msg":{"my_uid":"%s","opt_uid":"%s","token":"%s"}}
                """ % (self.uid, self.uid, self.token))
            log(ws.recv())

            ws.send(
                """3:::{"id":5,"route":"api.systemHandler.getUserDetail","msg":{"my_uid":"%s","user_detail_sync_tag":"",
                "token":"%s"}}"""
                % (self.uid, self.token))
            log(ws.recv())

            ws.send("""3:::{"id":6,"route":"api.systemHandler.getBrandNewConversation","msg":{"my_uid":"%s","opt_uid":"%s",
                "token":"%s"}}"""
                    % (self.uid, self.uid, self.token))
            log(ws.recv())

            ws.send(
                """3:::{"id":7,"route":"api.orgHandler.get_org_list","msg":{"my_uid":"%s","opt_uid":"%s","token":"%s"}}
                """ % (self.uid, self.uid, self.token))

            log(ws.recv())

        log(ws.recv())

        # get the url of young voice with token
        data = """3:::{"id":8,"route":"api.qnzsUserHandler.getQnzsChildUrl","msg":{"my_uid":"%s","share_url":
                "http://sns.qnzs.youth.cn/?token=","token":"%s"}}"""\
               % (self.uid, self.token)

        ws.send(data)
        data = ws.recv()
        log(data)

        json_data = json.loads(data[4:])
        young_voice_url = json_data["body"]["data"]["url"]
        self.young_voice_url = young_voice_url

        log(young_voice_url)

        if first_time:
            log('wait for one more time')
            log(ws.recv())
        ws.close()

    def extra_req(self):
        log('[INFO] simulate extra_req', 2, True)
        self.s.get('http://weibang.youth.cn/public/web/service/webmanager/getSiteType')

    def reg(self):
        self.login()
        self.websocket()
        self.extra_req()

    def check_voice_login(self):
        res = requests.get(self.young_voice_url)
        res.encoding = 'utf-8'
        if res.text.find('我的提问'):
            return True
        return False

    def bind_user_area(self):
        pass


if __name__ == "__main__":
    pass
