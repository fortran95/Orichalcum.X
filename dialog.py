#!/usr/bin/python
# -*- coding: utf-8 -*-
from Tkinter import *
import shelve
import os
import sys
import copy
import time
import tkMessageBox
import tkFileDialog
import threading
import random
import hashlib
import logging

from lockfile import FileLock

from widgets.richtextbox import RichTextBox,rich2plain
from widgets.dialogbox import DialogBox
import utils
import xisupport
import entity

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))
logger = logging.getLogger('orichalcumX.dialog')

FONT = ('sans',11)
class dialog(object):

    message_queue = []
    filter_hashes = []
    unhandled_receipts = []

    UNHANDLED_RECEIPT_COLOR = '#FCC'

    SECURITY_CONFIGS = [(('随便的谈话','#FF2400','#FFF'),(False,False,False)),
                        (('关注的谈话','#FF8C00','#000'),(True,False,False)),
                        (('重要的对话','#0070FF','#FFF'),(True,True,False)),
                        (('机密的对话','#4B0082','#FFF'),(True,True,True)),]
    security_choice = -1

    one_more_return = False

    def __init__(self,buddyname):
        global BASEPATH

        self.root = Tk()
        self.root.title(u'和 %s 对话中' % buddyname)
        self.buddyname = buddyname
        self.recordfile = os.path.join(BASEPATH,
                                       'cache',
                                       self.buddyname.encode('hex') + '.cache')
        
        # Lock Up Record File
        self.recordLock = FileLock(self.recordfile)
        try:
            self.recordLock.acquire(timeout=2)
        except:
            self.recordLock.break_lock()
            raise Exception('Unable to obtain dialog file lock. Is there another dialog already running?')

        self.createWidgets()
        
        # Center the Window and set it un-resizable.
        utils.center_window(self.root)
        self.root.resizable(0,0)
             
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.after(0,self.readMessages)
        self.root.mainloop()

    def ding(self):
        global BASEPATH
        path = os.path.join(BASEPATH,'alarms','notify.mp3')
        if os.path.isfile(path):
            try:
                os.system("mpg123 %s &" % path)
            except:
                pass

    def readMessages(self):
        global BASEPATH

        MSGDB_PATH0 = os.path.join(BASEPATH,'cache','msgdb.')
        lockfile = MSGDB_PATH0 + 'lock'
        shelvefile = MSGDB_PATH0 + 'db'

        if not os.path.isfile(lockfile):
            try:
                open(lockfile,'w+').write('a')
                sh = shelve.open(shelvefile,writeback=True)
                wantedkey = self.buddyname.strip().encode('hex')
                message_queue = []
                if sh.has_key(wantedkey):
                    newkeys = sh[wantedkey].keys()
                    for k in newkeys:
                        if k in self.filter_hashes:
                            del sh[wantedkey][k]
                    gotmessages = sh[wantedkey].values()
                    self.filter_hashes += sh[wantedkey].keys()
                    self.message_queue += sorted(gotmessages,
                                                 key=lambda x:x['info']['timestamp'])
                    del sh[wantedkey]
                    sh.close()
            except Exception,e:
                print str(e)
            os.remove(lockfile)

        # display messages    
        while self.message_queue:
            each = self.message_queue.pop(0)
            self.handle_received_message(False,**each)
        
        self.root.after(100,self.readMessages)
    
    def _timestr(self,timestamp=None):
        if timestamp == None:
            timestamp = time.time()
        return time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(timestamp))

    def handle_received_message(self,isOurs,**argv):
        print "Dialog: New message handling."
        try:
            if argv['info']['tag'] == 'im_receipt':
                recid = argv['message'].strip().lower()
                if recid in self.unhandled_receipts:
                    self.history.paintRecord(recid,self.history['background'])
                    self.unhandled_receipts.remove(recid)
            else:
                recordid = argv['info']['tag'][3:]
                if len(recordid) == 32: # Send response
                    self._send_core(recordid,
                                    'im_receipt',
                                    bool(argv['info']['xi']))
                self.append_message(isOurs,
                                    message=argv['message'],
                                    timestamp=argv['info']['timestamp'],
                                    xi=argv['info']['xi'])
                self.ding()
        except Exception,e:
            print e
            if not isOurs:
                self.history.newRecord(':: 收到一条错误消息 :: 长度%d字节 (%s)'
                                            %(len(argv['message']),
                                              self._timestr()),
                                       None,
                                       False)

    def append_message(self,isOurs,**each):
        #if not isOurs: raise Exception('') # Test only
        if isOurs:
            showname = '%s(我)' % utils.myname
        else:
            showname = self.buddyname
        headline = '%s %s:' % (showname,self._timestr(each['timestamp']))

        if type(each['message']) == str:
            recordid = self.history.newRecord(headline,each['message'],isOurs)
            if isOurs == False and each.has_key('xi') and each['xi'] == True:
                self.history.paintRecord(recordid,'#FFC800')
        else:
            raise Exception('')

        if self.historyScroll.get()[1] == 1.0:
            self.history.yview(END)
        
        return recordid

    def quit(self,e=None):
        global BASEPATH
        # Kill the dialog
        self.root.withdraw()
        if self.recordLock.i_am_locking():
            self.recordLock.release()
        self.root.destroy()

    def _onEOF(self,e=None):
        t = self.replybox.text()
        if bool(rich2plain(t).strip()):
            return
        self.quit()

    def _send_core(self,data,tag,crypt):
        cache = os.path.join(BASEPATH,
                             'cache',
                             hashlib.md5(str(data)
                                         +str(random.random())
                                        ).hexdigest()
                            )
        open(cache,'w').write(data)
        try:
            cmd1 = "python %s -r %s -i %s -t %s" % (os.path.join(BASEPATH,'send.py'),
                                                   self.buddyname,
                                                   cache,
                                                   tag)
            cmd2 = "python %s -f" % os.path.join(BASEPATH,'send.py')
            if crypt:
                cmd1 += ' -x'
            os.system(cmd1)
            os.system(cmd2)
        except Exception,e:
            print e
        os.remove(cache)
        
    def _do_send(self,crypt=True,receipt=False):
        global BASEPATH
        message = self.replybox.text()

        msglen = len(rich2plain(message).strip())
        if msglen <= 0 or msglen > utils.MAX_MESSAGE_LENGTH:
            self.replybox.flash(2)
            return

        # Add to history
        recordid = self.append_message(True,
                                       message=message,
                                       timestamp=time.time()
                                      ).strip().lower()
        if receipt:
            self.unhandled_receipts.append(recordid)
            self.history.paintRecord(recordid,self.UNHANDLED_RECEIPT_COLOR)
        else:
            recordid = 'x'
        self._send_core(message,'im_%s' % recordid,crypt)

        # clear input box
        self.replybox.clear()

    def _switch_level(self,events=None):
        self.security_choice += 1
        if self.security_choice >= len(self.SECURITY_CONFIGS):
            self.security_choice = 0
        profile = self.SECURITY_CONFIGS[self.security_choice]
        self.btnSecureLevel.config(text=profile[0][0],
                                   background=profile[0][1],
                                   foreground=profile[0][2])

        def cfg(obj,txt,status):
            if status:
                obj.config(text=txt[1],background='#0A0',foreground='#FFF')
            else:
                obj.config(text=txt[0],background='#A00',foreground='#FFF')

        cfg(self.showReceipt,('无回执','发送回执请求'),profile[1][0])
        cfg(self.showDefault,('明文发送','密文发送'),profile[1][1])
        cfg(self.showShortcut,('<Ctrl+Enter>','<Ctrl+Enter> X 2'),profile[1][2])
    def __resumeShortcutDisplay(self,e=None):
        self.showShortcut.config(font=FONT)
        self.one_more_return=False

    def _onSend(self,e=None):
        p = self.SECURITY_CONFIGS[self.security_choice]
        if p[1][2] and self.one_more_return == False:
            self.one_more_return = True
            self.showShortcut.config(font=FONT+('bold',))
            self.root.after(500,self.__resumeShortcutDisplay)
            return
        self.__resumeShortcutDisplay()
        self._do_send(bool(p[1][1]),bool(p[1][0]))

    def _onMenuClear(self,w):
        if w == self.history:
            self.history.clear()
        if w == self.replybox.textbox:
            self.replybox.clear()

    def _onMenu(self,e):
        w = e.widget
        self.quickmenu.entryconfigure("剪切",
                                      command=lambda: w.event_generate("<<Cut>>"))
        self.quickmenu.entryconfigure("复制",
                                      command=lambda: w.event_generate("<<Copy>>"))
        self.quickmenu.entryconfigure("粘贴",
                                       command=lambda: w.event_generate("<<Paste>>"))
        self.quickmenu.entryconfigure("清空",
                                       command=lambda: self._onMenuClear(w))
        self.quickmenu.tk.call("tk_popup",
                               self.quickmenu,
                               e.x_root,
                               e.y_root)

    def _createMenu(self):
        self.quickmenu = Menu(self.root, tearoff=0, font=FONT)
        self.quickmenu.add_command(label="剪切")
        self.quickmenu.add_command(label="复制")
        self.quickmenu.add_separator()
        self.quickmenu.add_command(label="粘贴")
        self.quickmenu.add_separator()
        self.quickmenu.add_command(label="清空")

    def createWidgets(self):      
        # Create Message Box
        self._createMenu()

        self.historyBox = Frame(self.root)
        self.historyBox.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.history = DialogBox(self.historyBox,height=20)
        self.historyBox.bind_class("Text","<Button-3><ButtonRelease-3>",
                                   self._onMenu)

        self.historyScroll = Scrollbar(self.historyBox,command=self.history.yview,width=16)
        self.history.config(yscrollcommand=self.historyScroll.set)
        
        self.historyScroll.pack(side=RIGHT,fill=Y)
        self.history.pack(side=RIGHT,fill=BOTH,expand=True)

        self.replybox = RichTextBox(self.root,width=80,height=8)
        self.replybox.textbox.bind_class("Text","<Button-3><ButtonRelease-3>",
                                         self._onMenu)
        self.replybox.grid(row=1,column=0,sticky=N+S+W+E)

        self.buttonframe = Frame(self.root,background='Black')
        self.buttonframe.grid(row=1,column=1,sticky=N+S+W+E,padx=2,pady=2)

        self.btnSecureLevel = Button(self.buttonframe,
                                     font=FONT,
                                     text='Secure: LOW',
                                     width=20,
                                     command=self._switch_level)
        showProperties = {'font':FONT,
                          'relief':RIDGE,
                         }
        self.showReceipt = Label(self.buttonframe,
                                 text='Receipt Required',
                                 **showProperties)
        self.showDefault = Label(self.buttonframe,
                                 text='Plain',
                                 **showProperties)
        self.showShortcut = Label(self.buttonframe,
                                  text='Ctrl+Enter',
                                  **showProperties)

        packProperties = {'padx':5,'pady':5,'ipadx':5,'ipady':5,'fill':BOTH,'expand':True}
        self.btnSecureLevel.pack(side=TOP,**packProperties)
        self.showReceipt.pack(side=TOP,**packProperties)
        self.showDefault.pack(side=TOP,**packProperties)
        self.showShortcut.pack(side=TOP,**packProperties)

        # Update the window.
        self.root.update_idletasks()

        self.replybox.bind('<F5>',self._switch_level)
        self.replybox.bind('<Control-Return>',self._onSend)
        self.replybox.bind('<Control-l>',self.replybox.clear)
        self.replybox.bind('<Control-d>',self._onEOF)
        self._switch_level()

if len(sys.argv) < 2:
    print 'usage: python dialog.py NAME_OF_YOUR_FRIEND'
    exit()

buddy = sys.argv[1].strip()
if entity.getJIDsByNickname(buddy) == False:
    print 'Unknown person. Please define persons(entities) in configs/alias.cfg.'
    exit()

try:
    frmMessage = dialog(sys.argv[1])
except Exception,e:
    print "Exit with error: %s" % e
except:
    print "Exit now."
