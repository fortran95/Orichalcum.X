# -*- coding: utf-8 -*-

from Tkinter import *
import shelve,os,sys,copy,base64,time,tkMessageBox,subprocess,tkFileDialog

from widgets.richtextbox import RichTextBox,rich2plain
from widgets.dialogbox import DialogBox
import utils

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

class message_list(object):
    def __init__(self,buddyname):
        self.root = Tk()
        self.root.title(u'和 %s 对话中' % buddyname)
        self.buddyname = buddyname
        self.createWidgets()
        
        # Center the Window and set it un-resizable.
        utils.center_window(self.root)
        self.root.resizable(0,0)
             
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.mainloop()
    def quit(self):
        global BASEPATH
        # Kill the dialog
        self.root.destroy()
    def testcommand(self):
        self.history.newrecord('line',self.replybox.text(),True)
    def createWidgets(self):      
        # Create Message Box
        self.history = DialogBox(self.root)
        self.history.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.replybox = RichTextBox(self.root,width=80,height=5)
        self.replybox.grid(row=1,column=0,rowspan=2)

        self.plainsend = Button(self.root,text=u'明文发送',width=20)
        self.plainsend.grid(row=1,column=1,sticky=N+S+E+W)
        self.plainsend['command'] = self.testcommand

        self.cryptsend = Button(self.root,text=u'加密发送')
        self.cryptsend.grid(row=2,column=1,sticky=N+S+E+W)
        
        # Update the window.
        self.root.update_idletasks()
    
frmMessage = message_list('orxszlyzr')
