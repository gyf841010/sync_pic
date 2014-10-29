#!/usr/bin/env python
#coding=utf8
from __future__ import division   # accurate division, must occur at the beginning of the file
import os   # os.path.exists()
from ctypes import *   # call c++ code
import tornado.database
import memcache
import yaml
import time
import logging
import logging.handlers

distance_threshold = 20
mh_distance_threshold = 0.40
strict_dist_threshold = 15
strict_mh_dist_threshold = 0.30

global_threshold = 0.86
total_threshold = 13.2

dct_mh_threshold = {'0': 0.40, '2': 0.40, '4': 0.40, '6': 0.40, '8': 0.40,
                    '10': 0.40, '12': 0.35, '14': 0.30, '16': 0.25, '18': 0.20, '20': 0.15}

pdll = CDLL('./libsim.so', RTLD_GLOBAL)
CDLL('./libpHash.so.0', RTLD_GLOBAL)
import pHash
result = create_string_buffer(8096)
srv = yaml.load(file('sp_config.yaml'))
mc = memcache.Client([srv['mem_cache']], debug=0)

def renew_db(db_master, sql):
    if db_master:
        try:
            db_master.close()
        except:
            pass
    db_master = tornado.database.Connection(host=srv['simpic_write_db'], database="simpic", user="slave", password="5jiu4xiejirong")
    db_master.execute(sql) 

def close_db(db_master):
    if db_master:
        try:
            db_master.close()
        except:
            pass

def fen(imgid, picture_file_name, file_name, _filterpic):
    """
return value         comment
-1      not exists picture file
-2      too little color
-3      not exist simlar picture
-4      simerror
-5      hasherror
-6      othererror

2       fentu
    """
    global pdll

    db_master = tornado.database.Connection(host=srv['simpic_write_db'], database="simpic", user="slave", password="5jiu4xiejirong")
    db_simpic = tornado.database.Connection(host=srv['simpic_read_db'], database="simpic", user="slave", password="5jiu4xiejirong")
    try:
        feature = db_simpic.query('select id, topcolor, totalcolor, width, height, dct from article_feature where id = %d' % imgid)
        mh_str = ""
        mh_list = []
        if len(feature) == 0:
            if not os.path.exists(file_name.strip()):
                return {"result": -1}

            hash = pHash.imagehash(file_name.strip())
            if hash:
                oldf = mc.get(str(hash))
                if oldf:
                    return oldf if oldf != 1 else {"result": 2}
            else:
                hash = "NULL"

            res = list()
            pdll._Simpic_GetFeature(file_name, result)
            ret = string_at(result)
            if ret:
                res = ret.split('\t')
            else:
                res.append("")
                res.append("1")
                res.append("1")
                res.append("")

            mh_list = pHash.mh_imagehash(file_name.strip())
            if mh_list:
                for item in mh_list:  # 将mh特征list转换成16进制字符串，方便存储
                    tmp = hex(item)[2:]
                    if len(tmp) == 1:
                        tmp = '0' + tmp
                    mh_str += tmp

            if hash != "NULL" and mh_str != "":
                sql = "insert ignore into article_feature set id = %d, topcolor = '%s', totalcolor = '%s', width=%s, " \
                      "height=%s, dct=%s;" % (imgid, res[0], res[3], res[2], res[1], hash)
                sql += 'insert into image_feature (id, topcolor, dct, mh, created_at) values ' \
                       '(%d, "%s", %d, "%s", now());' % (imgid, res[0], hash, mh_str)
                try:
                    db_master.execute(sql)
                except:
                    renew_db(db_master, sql)

            feature = [{'id': imgid, 'topcolor': res[0], 'totalcolor':res[3], 'width':int(res[2]),
                        'height':int(res[1]), 'dct':None if hash == "NULL" else hash}]

            if hash != "NULL":
                mc.set(str(hash), {"result": 2, 'oldid': imgid, 'topcolor': res[0],
                                   'distance': 0, 'mh_dist': -1, 'strategy': 1}, 172800)
        close_db(db_master)

        results = []
        if feature[0]['dct']:
            results = db_simpic.query('select id,topcolor,dct,bit_count(dct^%d) as dist '
                                     'from article_feature where topcolor="%s" and id<>%d and bit_count(dct^%d)<=%d '
                                     'order by bit_count(dct^%d),id desc limit 300;'
                        % (feature[0]['dct'], feature[0]['topcolor'], imgid, feature[0]['dct'], distance_threshold, feature[0]['dct']))

        if len(results) != 0 and feature[0]['dct']:
            id_list = [str(item['id']) for item in results]
            id_str = ','.join(id_list)
            more_info = db_simpic.query('select id,mh from image_feature where id in (%s)' % id_str)
            info = dict()
            for item in more_info:
                info[str(item['id'])] = item['mh']
            for r in results:
                if str(r['id']) in info and mh_list:
                    result_mh_list = []
                    for i in xrange(0, len(info[str(r['id'])]), 2):
                        result_mh_list.append(int(info[str(r['id'])][i:i + 2], 16))
                    mh_distance = pHash.hamming_distance2(mh_list, result_mh_list)
                    if mh_distance < mh_distance_threshold:
                        return {"result": 2, 'oldid': r['id'], 'topcolor': r['topcolor'],
                                'distance': r['dist'], 'mh_dist': mh_distance, 'strategy': 2}
                else:
                    if r['dist'] < strict_dist_threshold:
                        mh_distance = -1
                        return {"result": 2, 'oldid': r['id'], 'topcolor': r['topcolor'],
                                'distance': r['dist'], 'mh_dist': mh_distance, 'strategy': 2}

        if feature[0]['dct'] and "" != mh_str:
            interval = 2592000  # 30 days
            time_point = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - interval))
            results = db_simpic.query('select id,topcolor,dct,mh,bit_count(dct^%d) as dist from image_feature '
                                     'where id<>%d and bit_count(dct^%d)<=%d and created_at > "%s" '
                                     'order by bit_count(dct^%d),id desc limit 200;'
                                     % (feature[0]['dct'], imgid, feature[0]['dct'], distance_threshold, time_point, feature[0]['dct']))

            if len(results) != 0:
                for r in results:
                    result_mh_list = []
                    for i in xrange(0, len(r['mh']), 2):
                        result_mh_list.append(int(r['mh'][i:i + 2], 16))
                    mh_distance = pHash.hamming_distance2(mh_list, result_mh_list)
                    if mh_distance < dct_mh_threshold[str(r['dist'])]:
                        return {"result": 2, 'oldid': r['id'], "distance": r['dist'],
                                "mh_dist": mh_distance, 'topcolor': r['topcolor'], 'strategy': 3}

        return {"result": -3}

    except Exception, e:
        return {"result": -6, "exception": e}
    finally:
        close_db(db_master)
        close_db(db_simpic)
