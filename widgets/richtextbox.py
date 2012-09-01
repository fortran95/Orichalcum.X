# -*- coding: utf-8 -*-
import zlib
import threading
import time
from Tkinter import *

import bson

FONT = ('sans',11)

class RichTextBox(Frame):
    
    tagconfigs = [('B',   {'font':FONT + ('bold',)}),
                  ('H',   {'font':FONT + ('bold italic',)}),
                  ('H',   {'font':FONT + ('italic',)}),
                  ('_',   {'underline':True}),
                  ('红',  {'foreground':'#F00'}),
                  ('蓝',  {'foreground':'#00B'}),
                  ('绿',  {'foreground':'#070'}),
                 ]
    
    def __init__(self,root,**argv):
        Frame.__init__(self,root)
        self._createWidgets(**argv)

    def _createWidgets(self,**argv):
        self.editorbar = Frame(self)
        self.textbox = Text(self,font=FONT,**argv)
        self.editorbar.buttons = []

        for each in self.tagconfigs:
            self.editorbar.buttons.append(Button(self.editorbar,text=each[0],**each[1]))
            self.textbox.tag_config("tag%d" % self.tagconfigs.index(each),each[1])
            def _barbtn_action(b=self.editorbar.buttons[-1],tagname="tag%d" % self.tagconfigs.index(each)):
                try:
                    self.textbox.tag_add(tagname,SEL_FIRST,SEL_LAST)
                except:
                    pass
            self.editorbar.buttons[-1]['command'] = _barbtn_action
            self.editorbar.buttons[-1].pack(side=LEFT,anchor=W)

        self.editorbar.grid(column=0,columnspan=2,row=0)
        self.textbox.grid(row=1,column=0)

    def enable(self):
        self.textbox.config(state=NORMAL)

    def disable(self):
        self.textbox.config(state=DISABLED)

    def clear(self):
        self.textbox.delete(1.0,END)

    def flash(self,times,background='#F22'):
        def _flashfunc(t=times,bg=background):
            orig = self.textbox['background']
            interval = 0.10
            for i in range(0,t):
                self.textbox.config(background=bg)
                time.sleep(interval)
                self.textbox.config(background=orig)
                time.sleep(interval)
        threading.Timer(0,_flashfunc).start()

    def _inRange(self,tagname,probe):
        ranges = self.textbox.tag_ranges(tagname)
        probe = float(probe)
        ret = False
        for each in ranges:
            each = float(each)
            if each >= probe:
                return ret
            ret = not ret
        return ret

    def text(self):
        plaintext = zlib.compress(unicode(self.textbox.get(1.0,END)).encode('utf-8'),9)
        decorations = {}
        for each in self.tagconfigs:
            decid = str(self.tagconfigs.index(each))
            decorations[decid] = []
            ranges = self.textbox.tag_ranges("tag%d" % int(decid))
            for textindex in ranges:
                tib,tie = textindex.string.split('.')
                decorations[decid].append((int(tib),int(tie)))
        return bson.dumps({'t':plaintext,'d':decorations})

    def load(self,inp):
        def r(x):
            return "%d.%d" % (x[0],x[1])
        self.textbox.delete(1.0,END)
        j = bson.loads(inp)
        plaintext = zlib.decompress(j['t'])
        decorations = j['d']
        self.textbox.insert(END,plaintext)
        for tagname,indexlist in decorations.items():
            while indexlist:
                if len(indexlist) >= 2:
                    cstart,cend = [r(t) for t in indexlist[0:2]]
                    indexlist = indexlist[2:]
                else:
                    cstart = r(indexlist[0])
                    cend = END
                    indexlist = []
                self.textbox.tag_add("tag%d" % int(tagname),cstart,cend)

def rich2plain(inp):
    j = bson.loads(inp)
    return zlib.decompress(j['t'])
        

if __name__ == '__main__':
    root = Tk()
    a = RichTextBox(root)
    a.grid(row=0,column=0)
    b = Button(root,text='generate')
    b.grid(row=1,column=0)
    c = RichTextBox(root)
    c.grid(row=2,column=0)
    def cmd(x=a,y=c):
        text = x.text()
#        print rich2plain(text)
        y.load(text)
    b['command'] = cmd
    root.mainloop()
