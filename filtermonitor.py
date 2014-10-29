# -*- coding: utf-8 -*-
import os
import time
import requests

def send_simple_message(subject, content):
    return requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

if __name__ == '__main__':
    cmd = 'python filter_pic.py 1>/dev/null 2>/dev/null&'
    a = os.popen("ps -ef | grep filter_pic.py | awk '/\<filter_pic.py$/{ print }' | awk '{ if(NF==8 || NF>8 && index($(NF-1),\"python\")>0) print}'").read()

    if not a :
        os.system(cmd)
        time.sleep(3)
        a = os.popen("ps -ef | grep filter_pic.py | awk '/\<filter_pic.py$/{ print }' | awk '{ if(NF==8 || NF>8 && index($(NF-1),\"python\")>0) print}'").read()
        if not a :
            content = u'图片过滤服务无法启动'
            subject = u'图片过滤服务异常'
            send_simple_message(subject, content)
