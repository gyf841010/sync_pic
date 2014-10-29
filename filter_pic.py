#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import tornado.database
import logging
import logging.handlers
import time
import re
import gevent
import os
import traceback
from time import gmtime, strftime, localtime, time, mktime, sleep
from gevent.threadpool import ThreadPool
import requests
import sys
from log_sender import UdpLog, mpLogCmd
import yaml
import sqlite3

try:
    from PIL import Image
except ImportError:
    import Image
try:
    import fentu
except:
    print traceback.format_exc()
from multiprocessing import Pool, Process, Manager

# except: logging.info( "load fentu error" )

_filterpic = logging.getLogger('filterpic')
ch = logging.handlers.RotatingFileHandler('filter-pic.log')
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")  # format your msg
ch.setFormatter(formatter)
_filterpic.addHandler(ch)

reobj = re.compile("(.png|.bmp|.gif|.cgi|.jpeg|.JPG)", re.I)


def PicName(filename):
    filename = reobj.sub('.jpg', filename)
    return filename


def renew_db(db, sql):
    srv = yaml.load(file('sp_config.yaml'))
    if db:
        try:
            db.close()
        except:
            pass
    try:
        db = tornado.database.Connection(host=srv['mysql'], database='qqq1', user='slave', password='5jiu4xiejirong')
        db.execute(sql)
    except:
        _filterpic.warning("renew db connection failed")
        return
    _filterpic.warning("renew db connection success")


def close_db(qqq_db, fenreport_db):
    if qqq_db:
        try:
            qqq_db.close()
        except:
            pass
    if fenreport_db:
        try:
            fenreport_db.close()
        except:
            pass


def send_simple_message(subject, content):
    return requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})


def filter_fen(art, qqq_db, fenreport_db):
    ret = ""
    try:
        art['gid'] = int(art['id'] / 10000)
        p = "/home/www/qqq/current/public/system/pictures/%(gid)d/%(id)d/medium/" % art
        # p = "/home/gyf/pic_handle/medium/" % art
        m = (p + PicName(art['picture_file_name'])).encode("utf8")
        ret = fentu.fen(art['id'], m, m, _filterpic)
        _filterpic.warning("filter_fen: %d %s" % (art['id'], str(ret)))
        if ret['result'] == 2:
            updated_at = strftime("%Y-%m-%d %T", localtime(time()))
            sql = "update articles set status = 'private', updated_at = '%s' where id = %d;" % (updated_at, art['id'])
            try:
                ret_db = qqq_db.execute(sql)
                _filterpic.warning("filter_fen db update result: %d %s" % (art['id'], ret_db))
            except:
                _filterpic.warning("filter_fen: %d renew" % (art['id']))
                renew_db(qqq_db, sql)

            ret['aid'] = art['id']

            if 'mh_dist' in ret:
                sql_insert = "insert ignore into fenlist (aid,oldid,topcolor,simglobal,simtotal,distance) " \
                             "values (%(aid)d,%(oldid)d,'%(topcolor)s', " \
                             "%(mh_dist).3f, %(strategy).3f, %(distance)d);" % ret  # 为了不修改fenlist表的数据结构，
                # 在对坟图升级之后simglobal和simtotal
                # 两个字段用来存放新的mh_dist
                # 和strategy字段
            else:
                sql_insert = "insert ignore into fenlist (aid,oldid,topcolor,simglobal,simtotal,distance) " \
                             "values (%(aid)d,%(oldid)d,'%(topcolor)s', " \
                             "-1, 1, %(distance)d);" % ret  # 为了不修改fenlist表的数据结构，
                # 在对坟图升级之后simglobal和simtotal
                # 两个字段用来存放新的mh_dist
                # 和strategy字段
            try:
                ret_db = fenreport_db.execute(sql_insert)
                _filterpic.warning("filter_fen db insert result: %d %s" % (art['id'], ret_db))
            except:
                _filterpic.warning("filter_fen: insert faild! %d" % (art['id']))

            UdpLog(mpLogCmd['post_archieve'],
                   'id[%(aid)d] {fentu} {go private} olid[%(oldid)d] distance[%(distance)d]' % ret)
            _filterpic.warning("filter_fen: %d log sent" % (art['id']))

        return True
    except:
        _filterpic.warning(traceback.format_exc())
        return False


def filter_pic(arts, resList):
    srv = yaml.load(file('sp_config.yaml'))
    qqq_db = tornado.database.Connection(host=srv['qqq_write_db'], database='qqq1', user='slave', password='5jiu4xiejirong')
    fenreport_db = tornado.database.Connection(host=srv['qqq_write_db'], database='fenreport', user='slave', password='5jiu4xiejirong')
    for art in arts:
        try:
            if filter_fen(art, qqq_db, fenreport_db):
                resList.append({'result': 0, 'art': art})
            else:
                resList.append({'result': 2, 'art': art})
        except:
            _filterpic.warning(traceback.format_exc())
            resList.append({'result': 2, 'art': art})

    close_db(qqq_db, fenreport_db)


def delete_pic_from_db(cx, cu, art):
    try:
        cu.execute("delete from addpic_log where id= %s" % art['id'])
        cx.commit()
        _filterpic.warning("sqlite delete success: %s" % art['picture_file_name'])
    except:
        _filterpic.warning(traceback.format_exc())
        _filterpic.warning("sqlite delete error: %s" % art['picture_file_name'])


def delete_bad_case(cx, cu, row):
    try:
        cu.execute("delete from addpic_log where id= %s" % row[0])
        cx.commit()
        _filterpic.warning("sqlite delete success: %s" % row[0])
    except:
        _filterpic.warning(traceback.format_exc())
        _filterpic.warning("sqlite delete error: %s" % row[0])


def bad_pic_check(rows, resList, bad_pic_dict, cu, cx):
    rows_id = [int(row[0]) for row in rows]
    resList_id = [int(res['art']['id']) for res in resList]
    diff_id = list(set(rows_id).difference(set(resList_id)))  # 求差集

    for item in diff_id:
        if item in bad_pic_dict:
            bad_pic_dict[item] += 1
        else:
            bad_pic_dict[item] = 1

    limit = 3
    bad_pic_list = list()
    for key, value in bad_pic_dict.items():
        if value >= limit:
            bad_pic_list.append(key)

    for item in bad_pic_list:
        bad_pic_dict.pop(item)
        try:
            cu.execute("delete from addpic_log where id= %s" % item)
            cx.commit()
            _filterpic.warning("sqlite delete bad pic success: %s" % item)
        except:
            _filterpic.warning(traceback.format_exc())
            _filterpic.warning("sqlite delete bad pic error: %s" % item)


def main():
    try:
        cx = sqlite3.connect("/home/www/qqq/current/sync_pic/addpic.db")
        cu = cx.cursor()
        bad_pic_dict = dict()  # 坟图服务使用了一些C/C++扩展的so库，如果坟图处理core在so库中，异常是无法被捕捉的，需要一些额外的手段监控这些异常
                               # 这里的思路是维护一个失败图片的计数器，一旦图片多次失败，则将其干掉，不再处理了
        while 1:
            start_time = time()

            cu.execute("select * from addpic_log order by id desc limit 100")
            rows = cu.fetchall()
            print rows

            num = 5
            manager = Manager()
            resList = manager.list()
            threads = []
            for i in range(num):
                sub_rows = rows[i::num]
                arts = []
                for row in sub_rows:
                    try:
                        art = {"id": int(row[0]), 'picture_file_name': row[1]}
                    except:
                        _filterpic.warning("bad pic log: %s" % row[0])
                        delete_bad_case(cx, cu, row)
                        continue
                    arts.append(art)
                p = Process(target=filter_pic, args=(arts, resList,))
                threads.append(p)

            for i in range(num):
                threads[i].start()

            for i in range(num):
                threads[i].join()

            _filterpic.warning("rows len: %d; retlist len: %d" % (len(rows), len(resList)))
            bad_pic_check(rows, resList, bad_pic_dict, cu, cx)
            _filterpic.warning("bad_pic_dict: %s" % bad_pic_dict)
            for res in resList:
                try:
                    if res['result'] != 0:
                        _filterpic.warning("filter_failed %s" % res['art']['picture_file_name'])
                    else:
                        _filterpic.warning("filter_success %s" % res['art']['picture_file_name'])
                        delete_pic_from_db(cx, cu, res['art'])
                except:
                    _filterpic.warning("process error")

            wait_time = 10 - (time() - start_time)
            if wait_time > 0:
                _filterpic.warning("Will sleep %ds till next sync" % wait_time)
                sleep(wait_time)
            else:
                _filterpic.warning("Use too much time, starting next sync right now")

    except:
        content = traceback.format_exc()
        if content is None:
            content = ""
        else:
            content = content.replace('"', "'")
        subject = "Pic filter service down!"
        send_simple_message(subject, content)
        _filterpic.warning(content)


if __name__ == '__main__':
    main()

