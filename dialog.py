# -*- coding: utf-8 -*-
from Tkinter import *
import shelve,os,sys,copy,base64,time,tkMessageBox,subprocess,tkFileDialog,random,hashlib

from widgets.richtextbox import RichTextBox,rich2plain
from widgets.dialogbox import DialogBox
import utils
import xisupport

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
        self.root.destroy()
    def _do_send(self,message,crypt=True):
        global BASEPATH
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

    def send_plain(self):
        self._do_send(self.replybox.text(),False)
    def send_crypt(self):
        self._do_send(self.replybox.text(),True)

    def createWidgets(self):      
        # Create Message Box
        self.history = DialogBox(self.root)
        self.history.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.replybox = RichTextBox(self.root,width=80,height=5)
        self.replybox.grid(row=1,column=0,rowspan=2)

        self.plainsend = Button(self.root,text=u'明文发送',width=20,font=FONT)
        self.plainsend.grid(row=1,column=1,sticky=N+S+E+W)
        self.plainsend['command'] = self.send_plain

        self.cryptsend = Button(self.root,text=u'加密发送',bg='#FFC800',font=FONT)
        self.cryptsend.grid(row=2,column=1,sticky=N+S+E+W)
        self.cryptsend['command'] = self.send_crypt
        if not xisupport.XI_ENABLED:
            self.cryptsend['state'] = DISABLED
        
        # Update the window.
        self.root.update_idletasks()
    
frmMessage = message_list('orxszlyzr')
