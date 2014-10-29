#encoding: utf-8
import os
import tornado.database
import Image
import check_screenshot

def get_pic( x ):
    x['gid'] = int(x['id']/10000)
    ori = "/home/www/qqq/current/public/system/originals/%(picture_file_name)s"%x

    if not os.path.exists(ori):
        return None
    else:
        try:
            img = Image.open( ori )
        except:
            return None
    return img 

def get_pic_size( x ):
    img = get_pic( x )
    if img:
        return img.size

    return None

def check_crop_img( art ):
    img_size = get_pic_size( art )
    if not img_size :
        return {'result': -1, 'msg': 'no img size'}
    else:
        width, height = img_size
        if height/width >= 2:
            return {'result': 2, 'msg': 'height-width ratio is bigger than 2'}
    return {'result': 1, 'msg': 'height-width ratio is normal'}


def check_screenshot_img(art, db_mysql):
    #img = get_pic(art)
    #if not img:
    #    return {'result': -1, 'msg': 'no img'}
    #else:
    #    if check_screenshot.check_pic_test(img):
    #        msg = "the img is screenshot with size: %d*%d" % img.size
    #        return {'result': 2, 'msg': msg}
    #return {'result': 1, 'msg': 'the img is normal'}

    #db_mysql = tornado.database.Connection(host='203.195.194.53', database='qqq1', user='slave', password='5jiu4xiejirong')  # tx-db2
    sql = "select id,image_width,image_height,image_type,screen_width,screen_height from image_related where id=%d" % art['id']
    result = db_mysql.query(sql)
    #db_mysql.close()
    if len(result) != 0:
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




