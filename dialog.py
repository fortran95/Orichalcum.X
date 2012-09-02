# -*- coding: utf-8 -*-
from Tkinter import *
import shelve,os,sys,copy,base64,time,tkMessageBox,threading,tkFileDialog,random,hashlib

from widgets.richtextbox import RichTextBox,rich2plain
from widgets.dialogbox import DialogBox
import utils
import xisupport
import entity

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

FONT = ('sans',11)
class message_list(object):

    message_queue = []
    filter_hashes = []

    def __init__(self,buddyname):
        global BASEPATH

        self.root = Tk()
        self.root.title(u'和 %s 对话中' % buddyname)
        self.buddyname = buddyname
        self.recordfile = os.path.join(BASEPATH,'cache',self.buddyname.encode('hex') + '.cache')
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
                    self.message_queue += sorted(gotmessages,key=lambda x:x['timestamp'])
                    del sh[wantedkey]
                    sh.close()
            except Exception,e:
                print str(e)
            os.remove(lockfile)

        # display messages    
        while self.message_queue:
            each = self.message_queue.pop(0)
            self.append_message(False,**each)
        
        self.root.after(100,self.readMessages)
    
    def _timestr(self,timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(timestamp))

    def append_message(self,isOurs,**each):
        if isOurs:
            showname = '%s(我)' % utils.myname
        else:
            showname = self.buddyname
        headline = '%s %s:' % (showname,self._timestr(each['timestamp']))

        recordid = self.history.newRecord(headline,each['message'],isOurs)

        if isOurs == False and each.has_key('xi') and each['xi']:
            self.history.paintRecord(recordid,'#FFC800')


    def quit(self):
        global BASEPATH
        # Kill the dialog
        self.root.withdraw()
        self.root.destroy()
    def _do_send(self,message,crypt=True):
        global BASEPATH

        plainmessage = rich2plain(message).strip()
        if plainmessage == '':
            self.replybox.clear()
            self.replybox.flash(2)
            return

        cache = os.path.join(BASEPATH,'cache',hashlib.md5(message + str(random.random())).hexdigest())
        open(cache,'w').write(message)
        try:
            cmd = "python %s -r %s -i %s" % (os.path.join(BASEPATH,'send.py'),self.buddyname,cache)
            if crypt:
                cmd += ' -x'
            os.system(cmd)
        except Exception,e:
            print e
        os.remove(cache)

        # Add to history
        self.append_message(True,message=message,timestamp=time.time())

        # clear input box
        self.replybox.clear()

    def send_plain(self,events=None):
        self._do_send(self.replybox.text(),False)
        return
    def send_crypt(self,events=None):
        self._do_send(self.replybox.text(),True)

    def createWidgets(self):      
        # Create Message Box
        self.history = DialogBox(self.root)
        self.history.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.replybox = RichTextBox(self.root,width=80,height=5)
        self.replybox.grid(row=1,column=0)

        self.buttonframe = Frame(self.root,background='Red')
        self.buttonframe.grid(row=1,column=1,sticky=N+S+W+E)

        self.needReceipt = IntVar()
        self.needReceiptCheckbox = Checkbutton(self.buttonframe,
                                               text="选项：请求对方发送回执",
                                               padx=15,
                                               pady=10,
                                               variable=self.needReceipt,
                                               indicatoron=False,
                                               font=FONT)
#        self.needReceiptCheckbox.grid(row=0,column=0,sticky=N+S+E+W)
        self.needReceiptCheckbox.pack(side=TOP,fill=BOTH,expand=True)

        self.plainsend = Button(self.buttonframe,
                                text=u'明文发送',
                                padx=15,
                                pady=10,
                                font=FONT)
#        self.plainsend.grid(row=1,column=0,sticky=N+S+E+W)
        self.plainsend.pack(side=TOP,fill=BOTH,expand=True)
        self.plainsend['command'] = self.send_plain

        self.cryptsend = Button(self.buttonframe,
                                text=u'加密发送',
                                padx=15,
                                pady=10,
                                bg='#FFC800',
                                font=FONT)
#        self.cryptsend.grid(row=2,column=0,sticky=N+S+E+W)
        self.cryptsend.pack(side=TOP,fill=BOTH,expand=True)
        self.cryptsend['command'] = self.send_crypt
        if not xisupport.XI_ENABLED:
            self.cryptsend['state'] = DISABLED
        
        # Update the window.
        self.root.update_idletasks()

    def bindEvents(self):
        self.replybox.bind('<Control-Return>',self.send_plain)

if len(sys.argv) < 2:
    print 'usage: python dialog.py NAME_OF_YOUR_FRIEND'
    exit()
buddy = sys.argv[1].strip()
if entity.getJIDsByNickname(buddy) == False:
    print 'Unknown person. Please define persons(entities) in configs/alias.cfg.'
    exit()

frmMessage = message_list(sys.argv[1])
