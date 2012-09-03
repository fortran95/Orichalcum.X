# -*- coding: utf-8 -*-
from Tkinter import *
import threading
import json
import os
import sys
import time
import random
import hashlib

import utils
import notifier

configs = [(u'普通消息',{'bg':'#FFF'},{'fg':'#000'},{'fg':'#000'}),
           (u'快速情报',{'bg':'#7F9'},{'fg':'#000'},{'fg':'#000'}),
           (u'特殊事宜',{'bg':'#ADF'},{'fg':'#000'},{'fg':'#000'}),
           (u'紧急情况',{'bg':'#FC0'},{'fg':'#500'},{'fg':'#000'}),
           (u'危急警报',{'bg':'#A00'},{'fg':'#FC0'},{'fg':'#EEE'}),
          ]

class AlarmWindow(object):
    alarmcount = 0
    counting = True
    def __init__(self,quickview,level,info,desc,xi):
        if level not in range(0,len(configs)):
            raise Exception('Undefined config file.')
        self.level = level
        self.profile = configs[level]

        self.root = Tk()
        self._createWidgets(self.root,xi)

        self.root.title(self.profile[0])
        self.descBox.insert(END,desc.strip())
        self.descBox['state'] = DISABLED
        self.infoLabel['text'] = info

        self.quickview_title = unicode(quickview.strip())[0:self.quickview['width']]
        self.quickview.insert(END,self.quickview_title)
        self.quickview['state'] = DISABLED

        self.root.resizable(0,0)
        utils.center_window(self.root)
        self.root.after(0,self.afterJob)

        self.root.mainloop()

    def do_notify(self):
        notifier.osd(self.quickview_title,None,self.level)

    def afterJob(self):
        if self.counting:
            if self.alarmcount <= 0:
                self.alarmcount = 10
                # raise alarm
                threading.Timer(0,self.do_notify).start()

            self.button['text'] = '下一次声音告警将在 %d 秒后发出' % self.alarmcount
            self.alarmcount -= 1
            self.root.after(1000,self.afterJob)
    def buttonCommand(self,event=None):
        if self.counting:
            self.button['text'] = '点击关闭窗口'
            self.counting=False
        else:
            self.root.withdraw()
            self.root.destroy()
            exit()

    def _createWidgets(self,root,xi):
        root.config(**self.profile[1])

        self.quickview = Entry(root,**self.profile[2])
        self.quickview.config(font='sans 20 bold',
                              disabledbackground=root['background'],
                              disabledforeground=self.quickview['foreground'],
                              borderwidth=0,
                              relief=FLAT,
                              highlightthickness=0,
                              justify=CENTER,
                             )
        self.quickview.grid(row=0,column=0,padx=50,pady=15,sticky=W+E)

        self.bar1 = Frame(root,height=2,bd=1,relief=SUNKEN)
        self.bar1.grid(row=1,column=0,sticky=W+E,padx=10)

        self.infoLabel = Label(root,**self.profile[3])
        self.infoLabel.config(font='sans 10 bold',
                              background=root['background'])
        self.infoLabel.grid(row=2,column=0,padx=25,pady=5,sticky=W+E)

        self.descBox = Text(root,**self.profile[3])
        self.descBox.config(background=root['background'],
                            font='sans 12',
                            relief=FLAT,
                            width=80,
                            height=15,
                            borderwidth=0,
                            highlightthickness=0)
        self.descBox.grid(row=3,column=0,padx=25,pady=5,sticky=N+E+W+S)

        self.bar2 = Frame(root,height=2,bd=1,relief=SUNKEN)
        self.bar2.grid(row=4,column=0,sticky=W+E,padx=10)

        self.controlBox = Frame(root,bg=root['background'])

        self.controlinfo = Label(self.controlBox,**self.profile[3])
        self.controlinfo.config(text='来自 Orichalcum.X 信息系统   ',
                                font='sans 9',
                                background=self.controlBox['background'],)
        self.info_xi = Label(self.controlBox,**self.profile[3])
        self.info_xi.config(font='sans 9 bold',
                            background=self.controlBox['background'],
                            borderwidth=3,
                            relief=RIDGE,
                            justify=CENTER,
                            )
        if xi:
            self.info_xi['text'] = u'\u221a 加密信道'
        else:
            self.info_xi['text'] = u'X 明文信道'
        self.button = Button(self.controlBox)
        self.button.config(width=25,
                           font='sans 9',
                           command=self.buttonCommand)

        self.controlinfo.pack(side=LEFT)
        self.info_xi.pack(side=LEFT,padx=5,ipadx=3,ipady=3)
        self.button.pack(side=RIGHT)

        self.controlBox.grid(row=5,column=0,sticky=N+E+W+S,padx=15,pady=10)

        root.update_idletasks()

def handler(msg,**argv):
    try:
        j = json.loads(msg['message'])
        r = {}
        r['title'] = j['title']
        r['level'] = j['level']
        r['info'] = '报告人：%s  时间：%s' % (msg['sender'],
                                              time.strftime('%Y年%m月%d日 %H:%M:%S',
                                              time.gmtime(int(msg['info']['timestamp']))))
        r['body'] = j['body']
        r['xi'] = msg['info']['xi']

        # put to file and raise another process
        cachefile = os.path.join(utils.BASEPATH,
                                 'cache',
                                 hashlib.md5(str(time.time())
                                             +str(random.random())).hexdigest()
                                )
        open(cachefile,'w+').write(json.dumps(r))

        os.system('python %s %s'
                  % (os.path.join(utils.BASEPATH,
                                  'alarming.py'),
                     cachefile))

    except Exception,e:
        print "Alarming Plugin: Cannot raise alarm: %s" % e

def make_alarm(title,level,body):
    return json.dumps({'title':title,
                       'level':level,
                       'body':body})

if __name__ == '__main__':
    try:
        try:
            msgfile = sys.argv[1]
            j = json.loads(open(msgfile,'r').read())
            title = str(j['title']).strip()
            level = int(j['level'])
            info = str(j['info']).strip()
            body = str(j['body']).strip()
            xi = bool(j['xi'])
        except:
            print "Given file cannot be parsed."
            exit()
        AlarmWindow(title,level,info,body,xi)
    except Exception,e:
        print "Alarming Plugin: Unable to parse given file & raise alarm: %s" % e
