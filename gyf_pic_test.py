import os
import tornado.database
import logging
import logging.handlers
import time
import re
import gevent
import os
from gevent.threadpool import ThreadPool
import sys
sys.path.append("..")
import yaml
try:
  from PIL import Image
except ImportError:
  import Image
try:
    import check_screenshot_test 
except: logging.info( "load filter_img error" )

def get_pic( x ):
    x['gid'] = int(x['id']/10000)
    ori = "/home/gyf/pic_soft/original/%(picture_file_name)s"%x

    if not os.path.exists(ori):
        return None
    else:
        img = Image.open( ori )
    return img

def check_screenshot_img( art ):
    img = get_pic( art )
    if not img :
        return {'result': -1, 'msg': 'no img'}
    else:
        if check_screenshot_test.check_pic_test( img ):
            return {'result': 2, 'msg': 'the img is screenshot img'}
    return {'result': 1, 'msg': 'the img is normal'}

def filter_screenshotimg( art ):
    global db_master
    ret = ""
    try:
        ret = check_screenshot_img(art)
        if ret['result'] == 2:
            print("filter_screenshotimg: %d log sent" % (art['id']))
            return True
        else :    return False
    except:
        import traceback
        print( traceback.format_exc() )
        return False

    return False
 
def main():
    _DEBUG=True
    if _DEBUG == True:
        import pdb
        pdb.set_trace()
    addpic = "/home/gyf/pic_soft/addpic.log" 
    print "addpic log : " + addpic 

    cmd = "tail -n100 %s | awk '{print $NF}'" % addpic
    lines = os.popen( cmd ).readlines()

    for line in lines:
        try:
            art = {"id": int(line.replace("app","").split(".")[0]), 'picture_file_name': line.strip()}
        except:
            print("bad pic log: %s" % line)
        if filter_screenshotimg( art ):
            print "filter_screenshotimg",art['id'],'filtered'
                   
if __name__=="__main__":
    main() 
