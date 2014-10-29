# -*- coding: utf-8 -*-
import os
import sys
import StringIO
import time
import datetime
import traceback

# @gist import_io
import qiniu.io
# @endgist
import qiniu.conf
# @gist import_rs
import qiniu.rs
# @endgist
# @gist import_fop
import qiniu.fop
# @endgist
# @gist import_resumable_io
import qiniu.resumable_io as rio
# @endgist
# @gist import_rsf
import qiniu.rsf
# @endgist
# ----------------------------------------------------------

bucket_name = None
uptoken = None
domain = None

def setup():
    global bucket_name, uptoken, domain
    qiniu.conf.ACCESS_KEY = "sFh8m4CIWG1kzMhz0lcwi5E3mJ9Dq8U-sjNmYYey"
    qiniu.conf.SECRET_KEY = "zzUOkj6ELFys1jITX_qMLKWBnRi4aJ-jNpO2B6aT"
    bucket_name = "qiushibaike"
    domain = "pic.qiushibaike.com"
    # @gist uptoken
    policy = qiniu.rs.PutPolicy(bucket_name)
    uptoken = policy.token()
    # @endgist

def put_file(key, localfile):
    try:   
        setup()
        # 尝试删除
        qiniu.rs.Client().delete(bucket_name, key)

        ret, err = qiniu.io.put_file(uptoken, key, localfile)
        
        if err is not None:
            return {'result': 2, 'msg': err}
        return {'result': 0, 'msg': ret}
    except:
        msg = traceback.format_exc()
        return {'result': 2, 'msg': msg}


if __name__ == "__main__":
    put_file(key, localfile)







