from zhihu_oauth import ZhihuClient
from zhihu_oauth.exception import NeedCaptchaException
import json
import re

client = ZhihuClient()


def login_zhihu():
    try:
        client.login('496342862@qq.com', '7033675')
        client.save_token('token.pkl')
    except NeedCaptchaException:
        # 保存验证码并提示输入，重新登录
        with open('a.gif', 'wb') as f:
            f.write(client.get_captcha())
        captcha = input('please input captcha:')
        client.login('email_or_phone', 'password', captcha)


def get_zhihu_topic(topic_id):
    idarray = []
    client.load_token('token.pkl')
    topic = client.topic(topic_id)
    questions = []
    i = 0
    for ans in topic.best_answers:
        title = ans.question.title
        detail = ans.question.detail
        qid = ans.question.id
        if qid in idarray:
            print("dup")
            continue
        idarray.append(qid)
        i += 1
        re.sub(r'</?\w+[^>]*>', '', detail)
        re.sub(r'知乎', '青年之声', detail)
        if detail == "" or len(detail) > 30:
            detail = title

        questions.append({'question': title, 'answer': detail})
        print(i)
        if i > 250:
            break

    print(json.dumps(questions))

