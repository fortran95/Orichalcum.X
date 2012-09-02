# -*- coding: utf-8 -*-
import zlib
import threading
import time
from Tkinter import *

import bson

import _utils

class RichTextBox(Frame):
    
    tagconfigs = _utils.TAGCONFIGS
    font = _utils.FONT
    
    def __init__(self,root,**argv):
        Frame.__init__(self,root)
        self._createWidgets(**argv)

    def _createWidgets(self,**argv):
        self.editorbar = Frame(self)
        self.textbox = Text(self,font=self.font,**argv)
        self.textbox.config(foreground='#000',background='#FFF')
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
            self.editorbar.buttons[-1].pack(side=LEFT,anchor=W,fill=BOTH)

        self.editorbar.grid(column=0,columnspan=2,row=0,sticky=N+S+W+E)
        self.textbox.grid(row=1,column=0)

    def enable(self):
        self.textbox.config(state=NORMAL)

    def disable(self):
        self.textbox.config(state=DISABLED)

    def clear(self):
        self.textbox.config(foreground='#000',background='#FFF')
        self.textbox.delete(1.0,END)

    def bind(self,events,callback):
        self.textbox.bind(events,callback)

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

    def _stripText(self,text):
        text = text.rstrip()
        rowoffset = 0
        coloffset = 0
        while text:
            c = text[0]
            if c in ' \n':
                text = text[1:]
                if c in '\n':
                    rowoffset += 1
                    coloffset = 0
                if c in ' ':
                    coloffset += 1
            else:
                break
        return (text,rowoffset,coloffset)

    def text(self):
        stripped = self._stripText(self.textbox.get(1.0,END))
        #stripped = (self.textbox.get(1.0,END),0,0) # Test only
        plaintext = unicode(stripped[0]).encode('utf-8')
        plaintext = zlib.compress(plaintext,9)

        decorations = {}
        for each in self.tagconfigs:
            decid = str(self.tagconfigs.index(each))
            decorations[decid] = []
            ranges = self.textbox.tag_ranges("tag%d" % int(decid))
            for textindex in ranges:
                tib,tie = textindex.string.split('.')
                tib,tie = int(tib)-stripped[1],int(tie)
                if tib == 1:
                    tie -= stripped[2]
                decorations[decid].append((tib,tie))
        return bson.dumps({'t':plaintext,'d':decorations})

    def load(self,inp):
        self.textbox.delete(1.0,END)
        j = bson.loads(inp)
        plaintext = zlib.decompress(j['t'])

        stripped = self._stripText(plaintext)
        def r(x,r=stripped[1],c=stripped[2]):
            nr = x[0] - r
            if nr == 1:
                return "%d.%d" % (nr,x[1]-c)
            else:
                return "%d.%d" % (nr,x[1])

        decorations = j['d']
        self.textbox.insert(END,stripped[0])
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
    a = RichTextBox(root,height=5)
    a.grid(row=0,column=0)
    b = Button(root,text='generate')
    b.grid(row=1,column=0)
    c = RichTextBox(root,height=5)
    c.grid(row=2,column=0)
    def cmd(x=a,y=c):
        text = x.text()
#        print rich2plain(text)
        y.load(text)
    b['command'] = cmd
    root.mainloop()
