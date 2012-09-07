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
class message_list(object):

    message_queue = []
    filter_hashes = []
    unhandled_receipts = []

    UNHANDLED_RECEIPT_COLOR = '#FCC'

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
        self.bindEvents()
        
        # Center the Window and set it un-resizable.
        utils.center_window(self.root)
        self.root.resizable(0,0)
             
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.after(0,self.readMessages)
        self.root.mainloop()
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
        except Exception,e:
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

    def quit(self):
        global BASEPATH
        # Kill the dialog
        self.root.withdraw()
        if self.recordLock.i_am_locking():
            self.recordLock.release()
        self.root.destroy()
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
        
    def _do_send(self,message,crypt=True):
        global BASEPATH

        msglen = len(rich2plain(message).strip())
        if msglen <= 0 or msglen > utils.MAX_MESSAGE_LENGTH:
            self.replybox.flash(2)
            return

        # Add to history
        recordid = self.append_message(True,
                                       message=message,
                                       timestamp=time.time()
                                      ).strip().lower()
        if self.needReceipt.get():
            self.unhandled_receipts.append(recordid)
            self.history.paintRecord(recordid,self.UNHANDLED_RECEIPT_COLOR)
        else:
            recordid = 'x'
        self._send_core(message,'im_%s' % recordid,crypt)

        # clear input box
        self.replybox.clear()

    def send_plain(self,events=None):
        self._do_send(self.replybox.text(),False)
        return

    def send_crypt(self,events=None):
        self._do_send(self.replybox.text(),True)

    def createWidgets(self):      
        # Create Message Box
        self.historyBox = Frame(self.root)
        self.historyBox.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.history = DialogBox(self.historyBox,height=20)

        self.historyScroll = Scrollbar(self.historyBox,command=self.history.yview,width=16)
        self.history.config(yscrollcommand=self.historyScroll.set)
        
        self.historyScroll.pack(side=RIGHT,fill=Y)
        self.history.pack(side=RIGHT,fill=BOTH,expand=True)

        self.replybox = RichTextBox(self.root,width=80,height=8)
        self.replybox.grid(row=1,column=0,sticky=N+S+W+E)

        self.buttonframe = Frame(self.root,background='Red')
        self.buttonframe.grid(row=1,column=1,sticky=N+S+W+E,padx=2,pady=2)

        self.needReceipt = IntVar()
        self.needReceiptCheckbox = Checkbutton(self.buttonframe,
                                               padx=15,
                                               pady=10,
                                               width=15,
                                               highlightthickness=2,
                                               variable=self.needReceipt,
                                               indicatoron=False,
                                               font=FONT)
        self._normal_highlightcolor = self.needReceiptCheckbox['highlightbackground']
        def _onReceiptboxChecked(v1=None,mode=None,events=None):
            if self.needReceipt.get():
                self.needReceiptCheckbox.config(text='当前设定：请求回执',
                                                highlightbackground='#F00')
            else:
                self.needReceiptCheckbox.config(text='当前设定：不需回执',
                                                highlightbackground=self._normal_highlightcolor)
        self.needReceiptCheckbox.pack(side=TOP,fill=BOTH,expand=True)
        self.needReceipt.trace_variable('w',_onReceiptboxChecked)
        self.needReceipt.set(0)

        self.plainsend = Button(self.buttonframe,
                                text=u'明文发送\nCtrl+Shift+Enter',
                                padx=15,
                                pady=10,
                                highlightthickness=2,
                                font=FONT)
        self.plainsend.pack(side=TOP,fill=BOTH,expand=True)
        self.plainsend['command'] = self.send_plain

        self.cryptsend = Button(self.buttonframe,
                                text=u'加密发送\nCtrl+Enter',
                                padx=15,
                                pady=10,
                                highlightthickness=2,
                                bg='#FFC800',
                                font=FONT)
        self.cryptsend.pack(side=TOP,fill=BOTH,expand=True)
        self.cryptsend['command'] = self.send_crypt
        if not xisupport.XI_ENABLED:
            self.cryptsend['state'] = DISABLED
        
        # Update the window.
        self.root.update_idletasks()

    def bindEvents(self):
        self.replybox.bind('<Control-Return>',self.send_crypt)
        self.replybox.bind('<Control-Shift-Return>',self.send_plain)

if len(sys.argv) < 2:
    print 'usage: python dialog.py NAME_OF_YOUR_FRIEND'
    exit()

buddy = sys.argv[1].strip()
if entity.getJIDsByNickname(buddy) == False:
    print 'Unknown person. Please define persons(entities) in configs/alias.cfg.'
    exit()

try:
    frmMessage = message_list(sys.argv[1])
except Exception,e:
    print "Exit with error: %s" % e
except:
    print "Exit now."
