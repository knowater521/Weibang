import hashlib
import requests
import json
import time
from websocket import create_connection
from Expection import LoginFail
import config
import strings
import re
from tools import crypt, log


class Weibnag:
    username = ''
    password = ''
    uid = ''
    token = ''
    young_voice_url = ''
    young_token = ''
    selectedid = ''
    s = requests.session()
    young = requests.session()
    header = {"User-Agent": config.user_agent}
    young.headers = header
    s.headers = header
    debug = True

    def __init__(self, username='', password='', young_token=None):
        log('[INFO] user ' + username, 2, True)
        self.username = username
        self.password = password
        if young_token:
            self.young_token = young_token
            self.young_voice_url = "http://sns.qnzs.youth.cn/?token=" + young_token

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
            raise LoginFail()

        self.uid = userinfo['data']['uid']
        self.token = userinfo['data']['access_token']

    def websocket(self, first_time=False):
        log('[INFO] simulate web socket', 2, True)

        socket_detail = requests.get('http://123.103.5.50:9056/socket.io/1/?t=%d' % time.time() * 1000).text
        wsurl = 'ws://123.103.5.50:9056/socket.io/1/websocket/' + socket_detail.split(':')[0]

        ws = create_connection(wsurl)
        log(ws.recv())

        ws.send(strings.ws_string1 % (self.uid, self.username, self.token))
        log(ws.recv())

        if first_time:
            ws.send(strings.ws_string2 % (self.uid, self.token))
            log(ws.recv())

            ws.send(strings.ws_string3 % (self.uid, self.uid, self.token))
            log(ws.recv())

            ws.send(strings.ws_string4 % (self.uid, self.token))
            log(ws.recv())

            ws.send(strings.ws_string5 % (self.uid, self.uid, self.token))
            log(ws.recv())

            ws.send(strings.ws_string5 % (self.uid, self.uid, self.token))
            log(ws.recv())

        log(ws.recv())

        # get the url of young voice with token
        data = strings.ws_getvoice % (self.uid, self.token)

        ws.send(data)
        data_recv = ws.recv()
        log(data_recv)

        json_data = json.loads(data_recv[4:])
        if "id" not in json_data or json_data["id"] != 8:
            ws.send(data)
            data_recv = ws.recv()
            log(data_recv)
            json_data = json.loads(data_recv[4:])

        young_voice_url = json_data["body"]["data"]["url"]
        self.young_voice_url = young_voice_url
        self.young_token = young_voice_url.split('=')[-1]
        log(young_voice_url)

        if first_time:
            log('wait for one more time')
            time.sleep(5)
        ws.close()

    def reg(self):
        self.login()
        self.websocket(True)

    def check_voice_login(self, check_org=False):
        print("check_voice_login")
        res = self.young.get(self.young_voice_url)

        self.selectedid = res.url.split('/')[6]
        res.encoding = 'utf-8'
        print(res.text)
        if res.text.find('我的提问') != -1:
            if check_org:
                # 检测是否为正确的分区
                if res.text.find(config.org_name) != -1:
                    return True
            else:
                return True
        log(res.text)
        return False

    def bind_user_area(self):
        if self.young_voice_url == '' or self.young_token == '':
            self.login()
            self.websocket(False)

        log(self.young_voice_url, 2)

        post_data = config.org_switch_data.format(token=self.young_token)

        header = {
            "User-Agent": config.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://sns.qnzs.youth.cn/index/index/token/%s/limit" % self.young_token
        }
        res = self.young.post('http://sns.qnzs.youth.cn/ajax/changearea/token/' + self.young_token, data=post_data,
                              headers=header).json()
        log(res)
        if res["err"] == 0 and self.check_voice_login(True):
            log("[INFO]%s切换成功" % self.username, 2, True)

        else:
            log("[ERROR]%s切换失败" % self.username, 10, True)
            log(res)


    def post_question(self, title, content):
        if not self.check_voice_login():
            log("[ERROR]%s区域不正确" % self.username, 10, True)
            raise LoginFail("")
        res = self.young.get(
            "http://sns.qnzs.youth.cn/question/ask/token/{}/selectedid/{}/limit/0".format(self.young_token,
                                                                                          self.selectedid))
        res.encoding = 'utf-8'

        post_data = {"ques[title]": title,
                     "tags[]": "青年交流",
                     "ques[desc]": content}
        result = re.findall('<input type="hidden" name="([^"]+)" value="([^"]+)">', res.text, re.S)
        for item in result:
            post_data.update({item[0]: item[1]})

        header = {
            "User-Agent": config.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "Accept":"application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://sns.qnzs.youth.cn/question/ask/token/{}/selectedid/{}/limit/0".format(self.young_token,self.selectedid)
        }
        result = self.young.post("http://sns.qnzs.youth.cn/ajax/quessave/token/{}".format(self.young_token), data=post_data,
                               headers=header).json()
        log(result)

        pass


if __name__ == "__main__":
    pass
