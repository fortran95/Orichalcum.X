# -*- coding: utf-8 -*-
import zlib
from Tkinter import *

import bson

class RichTextBox(Frame):
    
    tagconfigs = {'b':('加粗',   {'foreground':'#F00'}),
                  'i':('斜体',   {}),
                  'u':('下划线', {'underline':True}),
                 }

    
    def __init__(self,root,**argv):
        Frame.__init__(self,root,**argv)
        self._createWidgets()

    def _createWidgets(self):
        self.editorbar = Frame(self)
        self.textbox = Text(self,height=10)
        self.editorbar.buttons = {}
        i = 0
        for key in self.tagconfigs:
            self.editorbar.buttons[key] = Button(self.editorbar,text=self.tagconfigs[key][0])
            self.textbox.tag_config(key,self.tagconfigs[key][1])
            def _barbtn_action(b=self.editorbar.buttons[key],tagname=key):
                self.textbox.tag_add(tagname,SEL_FIRST,SEL_LAST)
            self.editorbar.buttons[key]['command'] = _barbtn_action
            self.editorbar.buttons[key].pack(side=LEFT,anchor=W)
            i += 1


        self.editorbar.grid(column=0,columnspan=2,row=0)
        self.textbox.grid(row=1,column=0)

    def enable(self):
        self.config(state=NORMAL)

    def disable(self):
        self.config(state=DISABLED)

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
        for key in self.tagconfigs:
            decorations[key] = []
            ranges = self.textbox.tag_ranges(key)
            for textindex in ranges:
                tib,tie = textindex.string.split('.')
                decorations[key].append((int(tib),int(tie)))
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
                self.textbox.tag_add(tagname,cstart,cend)

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
        print rich2plain(text)
        y.load(text)
    b['command'] = cmd
    root.mainloop()
