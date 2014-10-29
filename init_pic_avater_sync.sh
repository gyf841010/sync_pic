#!/bin/bash
# create by Fatpa on 2014.03.27

yum install -y ImageMagick zlib zlib-devel libjpeg libjpeg-devel freetype freetype-devel opencv
easy_install gevent

if [ -d /usr/lib/python2.6/site_packages/PIL ]; then
    rm -rf /usr/lib/python2.6/site_packages/PIL 
fi

if [ -f /usr/lib/python2.6/site_packages/PIL.pth ]; then
    rm -f /usr/lib/python2.6/site_packages/PIL.pth
fi

wget http://effbot.org/downloads/Imaging-1.1.7.tar.gz
tar zxvf Imaging-1.1.7.tar.gz
/usr/bin/python2.6 ./Imaging-1.1.7/setup.py install 
rm -f Imaging-1.1.7 Imaging-1.1.7.tar.gz

yum install -y gstreamer unicap libdc1394

