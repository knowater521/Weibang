import hashlib
import requests
import json
import time
from websocket import create_connection
from Expection import LoginFail
import config
import strings
import re
import logging
from tools import crypt

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s'
                    )


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
        logging.info("user " + username)
        self.username = username
        self.password = password
        if young_token:
            self.young_token = young_token
            self.young_voice_url = "http://sns.qnzs.youth.cn/?token=" + young_token

    def login(self):
        logging.info("[INFO] simulate login from web")

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
        logging.debug(userinfo)
        userinfo = json.loads(userinfo)

        if userinfo['code'] != "200":
            logging.error(self.username + '密码错误')
            raise LoginFail()

        self.uid = userinfo['data']['uid']
        self.token = userinfo['data']['access_token']

    def websocket(self, first_time=False):
        logging.info('[INFO] simulate web socket')

        socket_detail = requests.get('http://123.103.5.50:9056/socket.io/1/?t=%d' % time.time() * 1000).text
        wsurl = 'ws://123.103.5.50:9056/socket.io/1/websocket/' + socket_detail.split(':')[0]

        ws = create_connection(wsurl)
        logging.debug(ws.recv())

        ws.send(strings.ws_string1 % (self.uid, self.username, self.token))
        logging.debug(ws.recv())

        if first_time:
            ws.send(strings.ws_string2 % (self.uid, self.token))
            logging.debug(ws.recv())

            ws.send(strings.ws_string3 % (self.uid, self.uid, self.token))
            logging.debug(ws.recv())

            ws.send(strings.ws_string4 % (self.uid, self.token))
            logging.debug(ws.recv())

            ws.send(strings.ws_string5 % (self.uid, self.uid, self.token))
            logging.debug(ws.recv())

            ws.send(strings.ws_string5 % (self.uid, self.uid, self.token))
            logging.debug(ws.recv())

        logging.debug(ws.recv())

        # get the url of young voice with token
        data = strings.ws_getvoice % (self.uid, self.token)

        ws.send(data)
        data_recv = ws.recv()
        logging.debug(data_recv)

        json_data = json.loads(data_recv[4:])
        if "id" not in json_data or json_data["id"] != 8:
            ws.send(data)
            data_recv = ws.recv()
            logging.debug(data_recv)
            json_data = json.loads(data_recv[4:])

        young_voice_url = json_data["body"]["data"]["url"]
        self.young_voice_url = young_voice_url
        self.young_token = young_voice_url.split('=')[-1]
        logging.debug(young_voice_url)

        if first_time:
            logging.info('wait for one more time')
            time.sleep(5)
        ws.close()

    def reg(self):
        self.login()
        self.websocket(True)

    def check_voice_login(self, check_org=False):
        logging.info("check_voice_login")
        res = self.young.get(self.young_voice_url)

        self.selectedid = res.url.split('/')[6]
        res.encoding = 'utf-8'
        if res.text.find('我的提问') != -1:
            if check_org:
                # 检测是否为正确的分区
                if res.text.find(config.org_name) != -1:
                    logging.debug("分区正确")
                    return True
            else:
                logging.debug("无需分区检测")
                return True
        logging.warning("用户{}检测登陆失败".format(self.username))
        logging.debug(res.text)
        return False

    def bind_user_area(self):
        if self.young_voice_url == '' or self.young_token == '':
            self.login()
            self.websocket(False)

        logging.info(self.young_voice_url)

        post_data = config.org_switch_data.format(token=self.young_token)

        header = {
            "User-Agent": config.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://sns.qnzs.youth.cn/index/index/token/%s/limit" % self.young_token
        }
        res = self.young.post('http://sns.qnzs.youth.cn/ajax/changearea/token/' + self.young_token, data=post_data,
                              headers=header).json()
        logging.debug(res)
        if res["err"] == 0 and self.check_voice_login(True):
            logging.info("%s切换成功" % self.username, 2, True)

        else:
            logging.debug("[ERROR]%s切换失败" % self.username)
            logging.debug(res)

    def post_question(self, title, content):
        if not self.check_voice_login(True):
            logging.warning("[ERROR]%s区域不正确" % self.username)
            raise LoginFail("%s区域不正确")
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
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://sns.qnzs.youth.cn/question/ask/token/{}/selectedid/{}/limit/0".format(self.young_token,
                                                                                                     self.selectedid)
        }
        result = self.young.post("http://sns.qnzs.youth.cn/ajax/quessave/token/{}".format(self.young_token),
                                 data=post_data,
                                 headers=header).json()
        if result["err"] != 0:
            logging.warning("提问失败！！" + result["msg"] + " " + title)
            if result["err"] == 2:
                logging.INFO("重试提问。")
                self.post_question(title + "求大家分享，谢谢。", content + "大家说说自己的看法吧。")
        else:
            logging.info("提问成功")

        logging.debug(result)


if __name__ == "__main__":
    pass
