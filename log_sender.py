#coding=utf-8
import struct, socket, sys, datetime, os

SERVER_ADDR = ('218.23.120.84', 10086)

mpLogCmd = { "post_archieve" : 0x01,
             "web_http_error" : 0x02,
             "app_http_error" : 0x03,
             "long_web_http_request" : 0x04,
             "long_app_http_request" : 0x05,
             "user_life_track" : 0x06,
             "insert_error" : 0x07,
             "send_mail_stat" : 0x08,
             "analysis" : 0x0A,
           }

def getIp():
    ipList = []
    var = os.popen('/sbin/ifconfig').read().split("\n\n")
    for item in var:
        #print item
        symble1 = "inet addr:"
        pos1 = item.find(symble1)
        if pos1 >= 0:
            #print "find it : ",pos1
            tmp1 = item[pos1+len(symble1):]
            ipList.append(tmp1[:tmp1.find(" ")])
    if not ipList:
        ipList.append("0.0.0.0")
    for ip in ipList:
        if not ip.startswith("192") and not ip.startswith("127"):
            return ip
    return ipList[0]

def UdpLog(cmd, log):
    ver = 0x01
    format = '!cci'
    log = str(datetime.datetime.now()).split(".")[0]\
        + " [" + getIp() + "] " + log
    buf = struct.pack(format, chr(ver), chr(cmd), len(log))
    if type(log).__name__ == "unicode":
        buf += log.encode("utf-8", "ignore")
    else:
        buf += log

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(0)
    s.sendto(buf, SERVER_ADDR)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "./exe cmd content"
        sys.exit(-1)

    UdpLog(int(sys.argv[1]), sys.argv[2])
