# -*- coding: utf-8 -*-

from Tkinter import *
import shelve,os,sys,copy,base64,time,tkMessageBox,subprocess,tkFileDialog

from widgets.richtextbox import RichTextBox,rich2plain
from widgets.dialogbox import DialogBox

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

class message_list(object):
    def __init__(self,buddyname):
        self.root = Tk()
        self.root.title(u'和 %s 对话中' % buddyname)
        self.buddyname = buddyname
        self.createWidgets()
        
        # Center the Window and set it un-resizable.
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws/2) - (w/2) # calculate position x, y
        y = (hs/2) - (h/2)
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.root.resizable(0,0)
             
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.mainloop()
    def quit(self):
        global BASEPATH
        # Kill the dialog
        self.root.destroy()
    def createWidgets(self):      
        # Create Message Box
        self.history = DialogBox(self.root)
        self.history.grid(row=0,column=0,columnspan=2,sticky=N+S+W+E)

        self.replybox = RichTextBox(self.root,width=80,height=25)
        self.replybox.grid(row=1,column=0)

        self.sendbutton = Button(self.root,text=u'发送')
        self.sendbutton.grid(row=1,column=1,sticky=N+S+E+W)
        
        # Update the window.
        self.root.update_idletasks()
    
frmMessage = message_list('orxszlyzr')
