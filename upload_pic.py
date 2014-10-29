import logging
import logging.handlers
import traceback
import requests
import sqlite3
import time
import re
import os
import sys
import yaml 
from time import gmtime, strftime, localtime, time, mktime, sleep
from upload_qiniu import put_file 
from multiprocessing import Pool, Process, Manager

_uploadpic = logging.getLogger('uploadpic')
ch = logging.handlers.RotatingFileHandler( 'uploadpic.log' ) 
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s") # format your msg
ch.setFormatter(formatter)
_uploadpic.addHandler(ch)

def send_simple_message(subject, content):
    return requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

reobj = re.compile("(.png|.bmp|.gif|.cgi|.jpeg|.JPG)", re.I)
def get_picname(filename):
    filename = reobj.sub( '.jpg', filename)
    return filename

def upload_pic_to_qiniu( art ):
    try:
        art['gid'] = int(art['id']/10000)
        pic_name = get_picname(art['picture_file_name'])
        g_path = "/home/www/qqq/current/public/system/pictures/%d" % art['gid']
        path = "/home/www/qqq/current/public/system/pictures/%(gid)d/%(id)d" % art
        small = "%s/small/" % path
        smallfile = small + pic_name
        medium = "%s/medium/" % path
        mediumfile = medium + pic_name

        m_key_pre = "system/pictures/%(gid)d/%(id)d/medium/" % art
        s_key_pre = "system/pictures/%(gid)d/%(id)d/small/" % art
        m_key = m_key_pre + pic_name
        s_key = s_key_pre + pic_name
        if not put_file(m_key, mediumfile):
            _uploadpic.warning( 'upload medium failed: %d' % art['id'])
            return False
        if not put_file(s_key, smallfile):
            _uploadpic.warning( 'upload small failed: %d' % art['id'])
            return False

    except:
        _uploadpic.warning("upload_pic except: %d" % art['id'])
        return False

    _uploadpic.warning("upload_pic success: %d" % art['id'])
    return True

def rsync_pic_to_center( art ):
    try:
        srv = yaml.load(file('sp_config.yaml'))
        group = int( int(art['id'])/10000 )
        loc = 'pictures/%d' % group
        cmd = ("rsync -r -ivh --timeout=30 /home/www/qqq/current/public/system/%s/%d %s::cgroom/%s/ "%(loc,art['id'],srv['other_pic_center'], loc))
        ret = os.system(cmd)
        if ret != 0:
            _uploadpic.warning("rsync pic failed: %s" % art)
            return False

    except:
        _uploadpic.warning("rsync pic except: %d" % art['id'])
        _uploadpic.warning( traceback.format_exc() )
        return False

    _uploadpic.warning("rsync pic success: %d" % art['id'])
    return True

def init_sqlite_db():
    cx = sqlite3.connect("/home/www/qqq/current/sync_pic/addpic.db")
    cu = cx.cursor()

    return cx, cu 

def sleep_in_loop( start_time ):
    wait_time = 5 - (time() - start_time)
    if wait_time>0:
        _uploadpic.warning("Will sleep %ds till next sync" % wait_time)
        sleep(wait_time)
    else:
        _uploadpic.warning("Use too much time, starting next sync right now")

def handle_subarts_in_pool( arts, resList ):
    for art in arts:
        try: 
            ret = {'result': 2, 'art': art}
            if upload_pic_to_qiniu( art ) and rsync_pic_to_center( art ):
                ret = {'result': 0, 'art': art}
        except:
            _uploadpic.warning( traceback.format_exc() )
            ret = {'result': 2, 'art': art}
        finally:
            resList.append(ret)

def handle_originals_in_multiprocessing( cx, cu, resList ):
    cu.execute("select * from qnpic_log limit 200")
    rows = cu.fetchall()

    num = 5
    proList = []
    for i in range(num):
        sub_rows = rows[i::num]
        arts = []
        for row in sub_rows:
            try:
                art = {"id": int(row[0]), 'picture_file_name': row[1]}
            except:
                _uploadpic.warning("bad pic log: %s" % row[0])
                continue
            arts.append(art)
        p = Process(target=handle_subarts_in_pool, args=(arts, resList,))
        proList.append(p)

    for i in range(num):
        proList[i].start()

    for i in range(num):
        proList[i].join(180)
        if proList[i].is_alive():
            _uploadpic.warning("process %d may hung" % i)
            proList[i].terminate()
            proList[i].join()

def delete_pic_from_db(cx, cu, art):
    try:
        cu.execute("delete from qnpic_log where id= %s" % art['id'])
        cx.commit()
        _uploadpic.warning("sqlite delete success: %s" % art['picture_file_name'])
    except:
        _uploadpic.warning(traceback.format_exc())
        _uploadpic.warning("sqlite delete error: %s" % art['picture_file_name'])

def handle_results( cx, cu, resList ):
    for res in resList:
        try:      
            if res['result']!= 0: #can not sync with any server
                _uploadpic.warning("handle_failed %s"%res['art']['picture_file_name'])
            else:
                _uploadpic.warning("handle_success %s"%res['art']['picture_file_name'])
                delete_pic_from_db(cx, cu, res['art'])
        except :  
            _uploadpic.warning("process reslist except, %s" % traceback.format_exc())

def init_process_list():
    manager = Manager()
    return manager.list()

def send_mail():
    content = traceback.format_exc()
    if content == None : content=""
    else: content = content.replace('"',"'")
    subject = "Pic handle service down!"
    send_simple_message(subject, content)
    _uploadpic.warning(content)

def main():
    try:        
        cx, cu = init_sqlite_db()
        
        while(True):
            start_time = time() 

            #this list an be shared between multiple processes
            resList = init_process_list()
            handle_originals_in_multiprocessing(cx, cu, resList)
            handle_results( cx, cu, resList )
            sleep_in_loop( start_time )

    except:
        send_mail()

if __name__ == '__main__':
    main()




