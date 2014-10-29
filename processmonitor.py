#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import requests
import os


def send_simple_message(subject, content):
    requests.post(
        "http://mail.moumentei.com/send/78687098@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

    requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})


def send_qiniu_message(subject, content):
    requests.post(
        "http://mail.moumentei.com/send/helishi@qiniu.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

    requests.post(
        "http://mail.moumentei.com/send/liujie@qiniu.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

    requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

cx = sqlite3.connect("/home/www/qqq/current/sync_pic/addpic.db")
cu = cx.cursor()
cu.execute("select * from addpic_log")
rows = cu.fetchall()
cu.execute("select * from qnpic_log")
qn_rows = cu.fetchall()

num_unprocessed = 200
print len(rows)
if len(rows) > num_unprocessed:
    subject = '坟图处理出现大量图片积压:%d' % len(rows)
    content = '坟图处理出现大量图片积压:%d' % len(rows)
    send_simple_message(subject, content)

print len(qn_rows)
if len(qn_rows) > num_unprocessed:
    subject = '上传七牛服务出现大量图片积压:%d' % len(qn_rows)
    content = '上传七牛服务处理出现大量图片积压:%d' % len(qn_rows)
    send_qiniu_message(subject, content)

o_dir = "/home/www/qqq/current/public/system/originals"
ori_list = os.listdir(o_dir)
print len(ori_list)
if len(ori_list) > num_unprocessed:
    subject = '图片同步处理出现大量图片积压:%d' % len(ori_list)
    content = '图片同步处理出现大量图片积压:%d' % len(ori_list)
    send_simple_message(subject, content)



