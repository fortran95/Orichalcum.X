# -*- coding: utf-8 -*-

# 显示聊天内容的对话框

from Tkinter import *
import hashlib
import zlib

import bson

FONT = ('sans',11)
class DialogBox(Text):

    tagconfigs = [('B',   {'font':FONT + ('bold',)}),
                  ('H',   {'font':FONT + ('bold italic',)}),
                  ('H',   {'font':FONT + ('italic',)}),
                  ('_',   {'underline':True}),
                  ('红',  {'foreground':'#F00'}),
                  ('蓝',  {'foreground':'#00B'}),
                  ('绿',  {'foreground':'#070'}),
                 ]

    def __init__(self,master,**options):
        Text.__init__(self,master,**options)
        self.config(padx=7,pady=5,font=FONT)

        self.tag_config('style.head.local',foreground='#00A',font=FONT+('bold',))
        self.tag_config('style.head.buddy',foreground='#A00',font=FONT+('bold',))

        for each in self.tagconfigs:
            self.tag_config("tag%d" % self.tagconfigs.index(each),each[1])

        self.config(state=DISABLED)

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


    def newRecord(self,headline,text,is_ours):
        self.config(state=NORMAL)
        recordid = hashlib.md5(headline + text).hexdigest()

        # Insert Headline
        self.insert(END,'\n')
        headline = headline.strip() + '\n'
        if is_ours:
            self.insert(END,headline,('style.head.local',recordid))
        else:
            self.insert(END,headline,('style.head.buddy',recordid))

        # Insert Text
        revealEND = self.index(END)
        offset = int(revealEND.split('.')[0])
        j = bson.loads(text)
        plaintext = zlib.decompress(j['t'])
        stripped = self._stripText(plaintext)

        def r(x,s=offset,r=stripped[1],c=stripped[2]):
            nr = x[0] - r
            print x[0],r
            if nr == 1:
                nc = x[1] - c
            else:
                nc = x[1]
            return "%d.%d" % (s + nr - 2,nc)

        decorations = j['d']
        self.insert(END,stripped[0] + '\n',recordid)
        for tagname,indexlist in decorations.items():
            while indexlist:
                if len(indexlist) >= 2:
                    cstart,cend = [r(t) for t in indexlist[0:2]]
                    indexlist = indexlist[2:]
                else:
                    cstart = r(indexlist[0])
                    cend = END
                    indexlist = []
                self.tag_add("tag%d" % int(tagname),cstart,cend)

        
        self.yview(END)
        self.config(state=DISABLED)
        return recordid

    def paintRecord(self,recid,color):
        self.tag_config(recid,background=color)
