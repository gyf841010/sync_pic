#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import tornado.database
import logging
import logging.handlers
import time
import re
import sqlite3
import traceback
from time import gmtime, strftime, localtime, time, mktime, sleep
from upload_qiniu import put_file
#from gevent.threadpool import ThreadPool
from multiprocessing import Pool
import requests
import sys
from log_sender import UdpLog, mpLogCmd
import yaml
try:
  from PIL import Image
except ImportError:
  import Image
try:
    import filter_img
except: logging.info( "load filter_img error" )
from multiprocessing import Pool, Process, Manager

_syncpic = logging.getLogger('syncpic')
ch = logging.handlers.RotatingFileHandler( 'sync-pic.log' ) 
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s") # format your msg
ch.setFormatter(formatter)
_syncpic.addHandler(ch)

_addpic = logging.getLogger('addpic')
ch = logging.handlers.RotatingFileHandler( 'addpic.log' ) 
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s") # format your msg
ch.setFormatter(formatter)
_addpic.addHandler(ch)

mark = '/home/www/qqq/current/sync_pic/watermark.png'
mark_s = '/home/www/qqq/current/sync_pic/watermark_s.png'

class Params( object ):
    def __init__( self, *args, **kwargs ) :
        art = kwargs.pop( 'art', None)
        art['gid'] = int(art['id']/10000)
        pic_name = kwargs.pop( 'pic_name', None)
        self.art = art
        self.ori = "/home/www/qqq/current/public/system/originals/%(picture_file_name)s"%art
        self.g_path = "/home/www/qqq/current/public/system/pictures/%d" % art['gid']
        self.path = "/home/www/qqq/current/public/system/pictures/%(gid)d/%(id)d" % art
        self.small = "%s/small/" % self.path
        self.smallfile = self.small + pic_name
        self.medium = "%s/medium/" % self.path
        self.mediumfile = self.medium + pic_name
        self.large = "%s/large/" % self.path
        self.largefile = self.large + pic_name
        self.thumb = "%s/thumb/" % self.path
        self.thumbfile = self.thumb + pic_name
        self.im = None

reobj = re.compile("(.png|.bmp|.gif|.cgi|.jpeg|.JPG)", re.I)
def get_picname(filename):
    filename = reobj.sub( '.jpg', filename)
    return filename

def close_db( qqq_write_db, qqq_read_db ):
    if qqq_write_db:
        try:
            qqq_write_db.close()
        except:
            pass
    if qqq_read_db:
        try:
            qqq_read_db.close()
        except:
            pass


def send_simple_message( subject, content ):
    return requests.post(
        "http://mail.moumentei.com/send/258257921@qq.com?token=sqwsq121wsqsw_12",
        data={"title": subject,
              "html": content})

def compress_pic( src, dest, size, limit, quality ):
    imsrc = Image.open(src)
    if imsrc.size[0] < size[0] and imsrc.size[1] < size[1] and os.path.getsize(src) < limit:
        os.system("cp %s %s"%(src,dest))
        return
    ssize = "%dx%d"%size
    os.system('convert -strip -quality %s%% -resize "%s>" %s %s' % (quality,ssize,src,dest))
    while( quality > 30 and os.path.getsize(dest) > limit):
        quality-=9
        os.system('convert -strip -quality %s%% -resize "%s>" %s %s' % (quality,ssize,src,dest))
        _syncpic.warning("try_quality%d%%_size@%d"%(quality,os.path.getsize(dest)))

def rescan_pic( art, file_name ):
    try:
        if os.path.exists(file_name):
            if art['picture_file_name'].find('app') < 0:  # not from app, water mark it
                os.system("composite -channel rgba -gravity Center -dissolve 60 %s %s %s" % (mark, file_name, file_name))
            image_size1 = os.path.getsize(file_name)
            os.system("jpegrescan -t -s -q %s %s" % (file_name, file_name))  # 对图片进行最终的无损压缩
            image_size2 = os.path.getsize(file_name)
            _syncpic.warning("lossless shrink %d: %d -> %d %fx"
                             % (art['id'], image_size1, image_size2, float(image_size1 - image_size2)/image_size1))
    except:
        _syncpic.warning("rescan_pic except: %d" % art['id'])
        return False

    return True

def upload_pic_to_qiniu( params ):
    try:
        m_key_pre = "system/pictures/%(gid)d/%(id)d/medium/" % params.art
        s_key_pre = "system/pictures/%(gid)d/%(id)d/small/" % params.art
        m_key = m_key_pre + get_picname(params.art['picture_file_name'])
        s_key = s_key_pre + get_picname(params.art['picture_file_name'])
        if not put_file(m_key, params.mediumfile):
            _syncpic.warning( 'upload medium failed: %d' % params.art['id'])
            return False
        if not put_file(s_key, params.smallfile):
            _syncpic.warning( 'upload small failed: %d' % params.art['id'])
            return False

    except:
        _syncpic.warning("upload_pic except: %d" % params.art['id'])
        return False

    return True

def delete_badpic( params ):
    try:
        qqq_write_db.execute('update articles set picture_file_name=NULL where id=%d'%params.art['id'])
    except :
        try :
            qqq_write_db.reconnect()
            qqq_write_db.execute('update articles set picture_file_name=NULL where id=%d'%params.art['id'])
        except:
            _syncpic.warning("delete_badpic reconnect db and update art null except, %d" % params.art['id'])
    finally:
        os.system("rm -f %s" % params.ori)

def generate_medium( params ):
    try:
        if not os.path.exists(params.mediumfile):
            os.system("mkdir -p %s" % params.medium)
            if params.art['picture_file_name'].find('JPEG') > 0 and params.im.size[0] <= 500 and params.im.size[1] <= 800:
                os.system('cp %s %s' % (params.ori, params.mediumfile))
            else:      
                try:  
                    compress_pic(params.ori, params.mediumfile, (500, 800), 90*1024, 95)
                except:
                    _syncpic.warning("compress_pic fail: %s" % params.mediumfile)
                    delete_badpic( params )
                    return False
            if not rescan_pic( params.art, params.mediumfile ):
                return False
    except:
        _syncpic.warning("generate_medium except: %d" % params.art['id'])
        return False

    return True
 
def generate_small( params ):
    try:
        if not os.path.exists(params.smallfile):
            os.system("mkdir -p %s" % params.small)
            try:
                compress_pic(params.ori, params.smallfile, (220, 352), 18*1024, 75)
            except:
                _syncpic.warning("compress_pic fail: %s" % params.smallfile)
                delete_badpic( params )
                return False
            if not rescan_pic( params.art, params.smallfile ):
                return False
    except:
        _syncpic.warning("generate_small except: %d" % params.art['id'])
        return False

    return True

def generate_pic_dirs( params ):
    try:
        if not os.path.exists(params.g_path):
            os.system("mkdir -p %s" % params.g_path)
            os.system("chown nobody:nobody %s" % params.g_path)
        #small
        if not generate_small(params):
            return False
        #medium
        if not generate_medium(params):
            return False

        os.system("chown -R nobody:nobody %s" % params.path)
    except:
        _syncpic.warning("generate_pic_dirs except: %d, %s" % (params.art['id'], traceback.format_exc()))
        return False

    return True

def update_pic_size( params, qqq_write_db ):
    try:
        small_info = list(Image.open(params.smallfile).size) + [os.path.getsize(params.smallfile)]
        medium_info = list(Image.open(params.mediumfile).size) + [os.path.getsize(params.mediumfile)]
        img_info = {
                    "s":small_info,
                    "m":medium_info
                   }
        qqq_write_db.execute("update articles set picture_content_type='%s' where id=%d"%(yaml.dump(img_info) ,params.art['id']) )
    except:
        _syncpic.warning("update sizes except, %d, %s" % (params.art['id'], traceback.format_exc()))

def get_im_from_ori( params, qqq_write_db ):
    if not os.path.exists(params.ori):
        _syncpic.warning("original pic dir is not exist, %s" % params.ori)
        return None
    try : im = Image.open(params.ori)
    except :
        try:
            qqq_write_db.execute('update articles set picture_file_name=NULL where id=%d'%params.art['id'])
        except :
            try :
                qqq_write_db.reconnect()
                qqq_write_db.execute('update articles set picture_file_name=NULL where id=%d'%params.art['id'])
            except:
                _syncpic.warning("reconnect db and update art null except, %d" % params.art['id'])
        finally:
            _syncpic.warning("open ori pic image except, %d" % params.art['id'])  
            delete_badpic( params )
            return None
    if im.format=='GIF':
        try:
            im.save(params.ori)
        except:
            _syncpic.warning("GIF pic except, %d" % params.art['id'])
            return None

    return im

def process_pic( art, qqq_write_db ):
    #resize pic into small 220x352, medium 500x800, large 1024x1024, thumb 140x140
    pic_name = get_picname(art['picture_file_name'])
    params = Params( art = art,  pic_name = pic_name)
    im = get_im_from_ori( params, qqq_write_db )
    if not im:
        return False
    params.im = im

    if not generate_pic_dirs( params ):
        return False

    update_pic_size( params, qqq_write_db )
    os.system("rm -f %s" % params.ori)
    
    _syncpic.warning("process_pic success, %d", art['id'])
    return True

def filter_cropimg( art, qqq_write_db ):
    ret = ""
    try:
        ret = filter_img.check_crop_img(art)
        _syncpic.warning("filter_cropimg: %d %s" % (art['id'], str(ret['msg'])))
        if ret['result'] == 2:
            updated_at = strftime( "%Y-%m-%d %T", localtime(time()) )
            sql = "update articles set status = 'private', updated_at = '%s' where id = %d;" % (updated_at, art['id'])
            sql += "update scores set status = 'private' where article_id= %d;" % art['id']
            #sql += "insert ignore into article_mark set aid = %d, source = 'cropimg_kill', created_at = now(), updated_at = now(), extra_info = 'cropimg'; "% art['id']
            try:
                ret_db = qqq_write_db.execute(sql)
                _syncpic.warning("filter_cropimg db result: %d %s" % (art['id'], ret_db))
                #print sql
            except:
                _syncpic.warning("filter_cropimg: %d reconnect" % (art['id']))
                qqq_write_db.reconnect()
                qqq_write_db.execute(sql)
            UdpLog(mpLogCmd['post_archieve'], 'id[%d] {filter_cropimg} {go private}' %art['id'])
            _syncpic.warning("filter_cropimg: %d log sent" % (art['id']))
            return True
        else :    return False
    except:
        _syncpic.warning("filter_cropimg except, %s" % traceback.format_exc())
        return False

    return False


def filter_screenshotimg_logic( art, qqq_read_db ):
    try:
        sql = "select id,source,image_width,image_height,image_type,screen_width,screen_height from image_related where id=%d" % art['id']
        result = []
        try:
            result = qqq_read_db.query(sql)
        except Exception, e:
            _syncpic.warning("filter_screenshotimg image_related error: %s" % e)
            srv = yaml.load(file('sp_config.yaml'))
            if qqq_read_db:
                try:
                    qqq_read_db.close()
                except:
                    pass
            qqq_read_db = tornado.database.Connection(host=srv['qqq_read_db'], database='qqq1', user='slave', password='5jiu4xiejirong')
            result = qqq_read_db.query(sql)

        if len(result) != 0:
            if 'ios' in result[0]['source']:
                ori = "/home/www/qqq/current/public/system/originals/%(picture_file_name)s" % art
                if not os.path.exists(ori):
                    return {'result': 1, 'msg': 'the img is not exist in path'}
                else:
                    img = Image.open(ori)
                    width, height = img.size
                    if (width == 422 and height == 750) \
                        or (height == 422 and width == 750) \
                        or (width == 500 and height == 750) \
                        or (height == 500 and width == 750):  # iphone屏幕尺寸{640, 1136}对应{422, 750}和{750, 422}，屏幕尺寸{640, 960}对应{500, 750}和{750, 500}
                        msg = "the img is screenshot with size: %d*%d, ios" % (width, height)
                        return {'result': 2, 'msg': msg}
                    else:
                        return {'result': 1, 'msg': 'the img is normal, ios'}
            else:
                image_width = int(result[0]['image_width'])
                image_height = int(result[0]['image_height'])
                screen_width = int(result[0]['screen_width'])
                screen_height = int(result[0]['screen_height'])
                if image_width != 0 and image_height != 0 and \
                    ((image_width == screen_width and image_height == screen_height)
                     or (image_width == screen_height and image_height == screen_width)):
                    msg = "the img is screenshot with size: %d*%d, screen size: %d*%d" % (image_width, image_height, screen_width, screen_height)
                    return {'result': 2, 'msg': msg}
                else:
                    return {'result': 1, 'msg': 'the img is normal'}
        else:
            return {'result': 1, 'msg': 'the img is normal, no data'}
    except:
        _syncpic.warning("filter_screenshotimg_logic except, %s" % traceback.format_exc())
        return {'result': 1, 'msg': 'error in filter_screenshotimg_logic'}

def filter_screenshotimg( art, qqq_write_db, ret ):
    try:
        _syncpic.warning("filter_screenshotimg: %d %s" % (art['id'], str(ret['msg'])))
        if ret['result'] == 2:
            updated_at = strftime( "%Y-%m-%d %T", localtime(time()))
            sql = "update articles set status = 'private', updated_at = '%s' where id = %d;" % (updated_at, art['id'])
            sql += "update scores set status = 'private' where article_id= %d;" % art['id']
            #sql += "insert ignore into article_mark set aid = %d, source = 'cscreenshotimg_kill', created_at = now(), updated_at = now(), extra_info = 'screenshotimg'; "% art['id']
            try:
                ret_db = qqq_write_db.execute(sql)
                _syncpic.warning("filter_screenshotimg db result: %d %s" % (art['id'], ret_db))
                #print sql
            except:
                _syncpic.warning("filter_screenshotimg: %d reconnect" % (art['id']))
                qqq_write_db.reconnect()
                qqq_write_db.execute(sql)
            UdpLog(mpLogCmd['post_archieve'], 'id[%d] {filter_screenshotimg} {go private}' % art['id'])
            _syncpic.warning("filter_screenshotimg: %d log sent" % (art['id']))
            return True
        else:
            return False
    except:
        _syncpic.warning("filter_screenshotimg except, %s" % traceback.format_exc())
        return False


def handle_artSubList_in_process( arts, resList ):
    srv = yaml.load(file('sp_config.yaml'))
    qqq_read_db = tornado.database.Connection( host=srv['qqq_read_db'], database='qqq1', user='slave', password='5jiu4xiejirong')
    qqq_write_db = tornado.database.Connection( host=srv['qqq_write_db'], database='qqq1', user='slave', password='5jiu4xiejirong')
    for art in arts:
        try: 
            ret = {'result': 2, 'art': art}
            flag = False
            if filter_cropimg(art, qqq_write_db):
                flag = True 
            if not flag:
                result = filter_screenshotimg_logic(art, qqq_read_db)
                if filter_screenshotimg(art, qqq_write_db, result):
                    flag = True
            if process_pic(art, qqq_write_db):
                ret = {'result': 0, 'art': art}
        except:
            _syncpic.warning( traceback.format_exc() )
            ret = {'result': 2, 'art': art}
        finally:
            resList.append(ret)
    close_db( qqq_write_db, qqq_read_db )

def insert_pic_to_fendb( cx, cu, art ):
    try:
        cu.execute("insert into addpic_log values (%(id)d, '%(picture_file_name)s')" % art)
        cx.commit()
        _syncpic.warning("sqlite fen insert success: %s"% art['picture_file_name'])
    except:
        _syncpic.warning( traceback.format_exc() )
        _syncpic.warning("sqlite fen insert error: %s"% art['picture_file_name'])  

def insert_pic_to_qndb( cx, cu, art ):
    try:
        cu.execute("insert into qnpic_log values (%(id)d, '%(picture_file_name)s')" % art)
        cx.commit()
        _syncpic.warning("sqlite qiniu insert success: %s"% art['picture_file_name'])
    except:
        _syncpic.warning( traceback.format_exc() )
        _syncpic.warning("sqlite qiniu insert error: %s"% art['picture_file_name']) 

def send_mail():
    content = traceback.format_exc()
    if content == None : content=""
    else: content = content.replace('"',"'")
    subject = "Pic handle service down!"
    send_simple_message(subject, content)
    _syncpic.warning(content)  

def handle_originals_in_pool( pool, resList ):
    o_dir = "/home/www/qqq/current/public/system/originals"
    ori_list = os.listdir(o_dir)

    for ori in ori_list:
        try:
            art = {"id": int(ori.replace("app","").split(".")[0]), 'picture_file_name': ori.strip()}
        except:
            _syncpic.warning("bad pic log: %s" % ori)
            continue
        #res = pool.spawn(handle_pic, art)
        res = pool.apply_async(handle_pic_in_process, (art,))
        resList.append(res)

    pool.close()
    pool.join()

def get_artsublist_from_orilist( i, num, oriList ):
    artSubList = []
    subList = oriList[i::num]
    print subList
    for ori in subList:
        try:
            art = {"id": int(ori.replace("app","").split(".")[0]), 'picture_file_name': ori.strip()}
        except:
            _syncpic.warning("bad pic log: %s" % ori)
            continue
        artSubList.append(art)

    return artSubList

def init_process_list():
    manager = Manager()
    return manager.list()

def handle_originals_in_multiprocessing( resList ):
    oriDir = "/home/www/qqq/current/public/system/originals"
    oriList = os.listdir(oriDir)
    oriList = oriList[-1:-100:-1]
    proList = []
    num = 5
    for i in range(num):
        artSubList = get_artsublist_from_orilist(i, num, oriList)
        p = Process(target=handle_artSubList_in_process, args=(artSubList, resList,))
        proList.append(p)
        p.start()

    for i in range(num):
        proList[i].join(180)
        if proList[i].is_alive():
            _syncpic.warning("process %d may hung" % i)
            proList[i].terminate()
            proList[i].join()


'''
def handle_originals_direct():
    _DEBUG=True
    if _DEBUG == True:
        import pdb
        pdb.set_trace()
    o_dir = "/home/www/qqq/current/public/system/originals"
    ori_list = os.listdir(o_dir)

    for ori in ori_list:
        try:
            art = {"id": int(ori.replace("app","").split(".")[0]), 'picture_file_name': ori.strip()}
        except:
            _syncpic.warning("bad pic log: %s" % ori)
            continue
        if handle_pic( art ):
            _syncpic.warning("handle_originals_direct failed %s" % art['id'])
'''

def handle_results( cx, cu, resList ):
    for res in resList:
        try:      
            if res['result']!= 0: #can not sync with any server
                _syncpic.warning("handle_failed %s"%res['art']['picture_file_name'])
            else:
                _syncpic.warning("handle_success %s"%res['art']['picture_file_name'])
                _addpic.warning("handle_success %s"%res['art']['picture_file_name'])
                insert_pic_to_fendb(cx, cu, res['art'])
                insert_pic_to_qndb(cx, cu, res['art'])
        except :  
            _syncpic.warning("process reslist except, %s" % traceback.format_exc())

def sleep_in_loop( start_time ):
    wait_time = 5 - (time() - start_time)
    if wait_time>0:
        _syncpic.warning("Will sleep %ds till next sync" % wait_time)
        sleep(wait_time)
    else:
        _syncpic.warning("Use too much time, starting next sync right now")

def init_sqlite_db():
    cx = sqlite3.connect("/home/www/qqq/current/sync_pic/addpic.db")
    cu = cx.cursor()
    cu.execute("create table if not exists addpic_log (id int(11) NOT NULL primary key, picture_file_name varchar(255) DEFAULT NULL)")
    cu.execute("create table if not exists qnpic_log (id int(11) NOT NULL primary key, picture_file_name varchar(255) DEFAULT NULL)")

    return cx, cu

def main():
    try:        
        cx, cu = init_sqlite_db()
        
        while(True):
            start_time = time() 

            '''
            pool = Pool(processes=5)
            resList = []
            handle_originals_in_pool( pool, resList )
            handle_results( cx, cu, resList ) 
            '''

            #handle_originals_direct()

            #this list an be shared between multiple processes
            resList = init_process_list()
            handle_originals_in_multiprocessing(resList)
            handle_results( cx, cu, resList )
            sleep_in_loop( start_time )

    except:
        send_mail()

if __name__ == '__main__':
    main()

