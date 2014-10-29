#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

tmp_path = '/tmp'
now_time = time.time()
limit_time = now_time - 3600
files = os.listdir(tmp_path)
for item in files:
    if 'pymp' in item:
        full_path = '%s/%s' % (tmp_path, item)
        m_time = os.stat(full_path).st_mtime
        if m_time < limit_time:
            os.popen('rm -rf %s' % full_path)
            print full_path
