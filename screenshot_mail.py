#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import os
import random
import requests

day_point = str(datetime.datetime.now() - datetime.timedelta(days=1))[:10]
log_file = '/home/www/qqq/current/sync_pic/sync-pic.log'
cmd = "cat %s|grep %s|grep filter_screenshotimg|grep normal|awk '{print $5}'" % (log_file, day_point)
pic_list = os.popen(cmd).readlines()
pic_set = set([item.strip() for item in pic_list])
num_pics = len(pic_set)
print num_pics
cmd = "cat %s|grep %s|grep filter_screenshotimg|grep 'no data'|awk '{print $5}'" % (log_file, day_point)
nodata_pic_list = os.popen(cmd).readlines()
nodata_pic_set = set([item.strip() for item in nodata_pic_list])
num_nodata_pics = len(nodata_pic_set)
print num_nodata_pics
cmd = 'cat %s|grep %s|grep filter_screenshotimg|grep "screenshot with"' % (log_file, day_point)
filtered_pics_log = os.popen(cmd).readlines()
num_filtered_pics = len(filtered_pics_log)
print num_filtered_pics
html = "<h2>%s</h2>" \
       "<h2>截屏图过滤</h2>" \
       "<p>参与截屏图过滤的图片数：%d</p>"\
       "<p>无数据的图片数（无数据可能的原因是图片来源于web或者客户端版本较低）：%d</p>"\
       "<p>被判定为截屏图的数量为：%d，占比：%d%%</p>"\
    % (day_point, num_pics+num_filtered_pics, num_nodata_pics, num_filtered_pics, int(float(num_filtered_pics)/(num_pics+num_filtered_pics)*100))

html += "<h2>截屏图过滤采样</h2>"
tmp = range(num_filtered_pics)
random_list = random.sample(tmp, 20)
i = 1
for item in random_list:
    log_line = filtered_pics_log[item].strip()
    filtered_id = log_line.split()[4]
    html += "<p>%d. id: %s<br>" % (i, filtered_id)
    html += '<img src="http://pic.qiushibaike.com/system/pictures/%d/%s/medium/app%s.jpg" width="300"><br><br></p>' \
            % (int(filtered_id)/10000, filtered_id, filtered_id)
    i += 1

subject = u"糗百截屏图过滤"
requests.post("http://mail.moumentei.com/send/appannie@googlegroups.com?token=sqwsq121wsqsw_12",
#requests.post("http://mail.moumentei.com/send/78687098@qq.com?token=sqwsq121wsqsw_12",
              data={"title": subject, "html": html})






