# -*- coding: utf-8 -*-
from Tkinter import *
import pynotify
import time,subprocess,os,sys

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

def osd(message,desc=None,level=0):
    global BASEPATH

    if level in range(0,5):
        notifile = ['notify.mp3','caution.mp3','warning.mp3','alarm.mp3','danger.mp3'][level]
    else:
        return

    ns = subprocess.Popen(['mpg123','-q',os.path.join(BASEPATH,'alarms',notifile)])
    for i in range(0,3):
        osd_write(message,450.0)
    if desc != None:
        ns = subprocess.Popen(['mpg123','-q',os.path.join(BASEPATH,'alarms','notify.mp3')])
        for key in desc:
            osd_write(key,1500.0)
    
def osd_write(message,timed=450.0):
    ps = subprocess.Popen('gnome-osd-client -fs',shell=True,stdin=subprocess.PIPE)
    ps.stdin.write("""<message id='test' hide_timeout='%d' osd_vposition='top' osd_halignment='center'>\n\n<span foreground='#FF0000'>%s</span></message>""" % (timed,message))
    ps.communicate()
    time.sleep((timed + 150) / 1000)
def gnotify(message,desc):
    global BASEPATH
    ns = subprocess.Popen(['mpg123','-q',os.path.join(BASEPATH,'alarms','caution.mp3')])
    pynotify.init("Orichalcum")
    n = pynotify.Notification(message,desc)
    n.set_urgency(pynotify.URGENCY_NORMAL)
    n.set_timeout(15)
    n.show()
    time.sleep(1)
    
if __name__ == '__main__':
#    osd('未读消息：3条')
    osd('地震速报',['2008年5月12日 午后2时28分','四川省汶川县发生7.8级地震'],2)
    """
    def callback():
        print "Clicked!"
    gnotify("New message","content",callback)
    showMessage('a','b')
    """
