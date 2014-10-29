#encoding: utf-8
import os
import Image                                                                                                                        
import logging
import yaml

#通过百度统计可以获取如下用户使用手机尺寸的top信息
screen_shot_size = [(640, 960),  # iphone4
                    (1136, 640),  # iphone5
                    (720, 1280),
                    (480, 800),  # WVGA
                    (480, 854),  # FWVGA
                    (540, 960),
                    (1080, 1920),
                    (320, 480),  # HVGA
                    (800, 1280),
                    (720, 1184),
                    (1080, 1800),
                    (540, 888),
                    (1080, 1776),
                    (480, 782),
                    (640, 960),  # DVGA
                    (480, 728),
                    (480, 960),
                    (240, 320),  # QVGA
                    (720, 1208),
                    (600, 976),
                    (768, 1184),
                    (540, 894),
                    (720, 1200),
                    (600, 1024),
                    (800, 1232),
                    #(1440, 2560),
                    (768, 976),
                    (1200, 1824),
                    (768, 1280),
                    (1080, 1824),
                    (768, 1024),
                    (800, 1216),
                    (480, 752),
                    (480, 735),
                    #(1536, 1952),
                    (800, 1205),
                    (1200, 1848),
                    (480, 858),
                    #(1600, 2560),
                    (480, 764),
                    (240, 400),  # WQVGA2
                    (480, 806)
                    ]

def check_pic( img ):
    width, height = img.size
    sum_rgb = [0,0,0]
    arg_rgb = [0,0,0]
    items = []
    for i in range (1, width, 20):
        box = (i , 1)
        try:
            rgb = img.getpixel(box)
            items.append(rgb)
        except : 
            return False
        try:
            sum_rgb[0] += rgb[0]
            sum_rgb[1] += rgb[1]
            sum_rgb[2] += rgb[2]
        except : 
            return False
    count = len(items)
    arg_rgb[0] = sum_rgb[0]/count
    arg_rgb[1] = sum_rgb[1]/count
    arg_rgb[2] = sum_rgb[2]/count
    if arg_rgb[0] < 10 and arg_rgb[1] < 10 and arg_rgb[2] < 10:
        return True

    return False

def check_pic_test(img):
    width, height = img.size
    #for size in screen_shot_size:
        #if (width == size[0] and height == size[1]) or (height == size[0] and width == size[1]):
            #return True
    if check_pic_row(img, 1) and not check_pic_row(img, 15):
        return True
    return False

def check_pic_row( img, height_pos ):
    width, height = img.size
    
    if height_pos > height:
        return False
    
    sum_rgb = [0,0,0]
    arg_rgb = [0,0,0]
    items = []
    for i in range (1, width, 20):
        box = (i , height_pos)
        try:
            rgb = img.getpixel(box)
            items.append(rgb)
        except : 
            return False
        try:
            sum_rgb[0] += rgb[0]
            sum_rgb[1] += rgb[1]
            sum_rgb[2] += rgb[2]
        except : 
            return False
    count = len(items)
    arg_rgb[0] = sum_rgb[0]/count
    arg_rgb[1] = sum_rgb[1]/count
    arg_rgb[2] = sum_rgb[2]/count
    if arg_rgb[0] < 10 and arg_rgb[1] < 10 and arg_rgb[2] < 10:
        return True

    return False


