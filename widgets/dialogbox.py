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

    def newRecord(self,headline,text,is_ours):
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
        def r(x,s=offset):
            return "%d.%d" % (x[0]+s-2,x[1])
        j = bson.loads(text)
        plaintext = zlib.decompress(j['t'])
        decorations = j['d']
        self.insert(END,plaintext,recordid)
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
        return recordid

    def paintRecord(self,recid,color):
        self.tag_config(recid,background=color)

if __name__ == '__main__':
    root = Tk()
    box = DialogBox(root)
    box.pack(expand=1,fill=BOTH)
    #box.require_receipt = False
    box.newrecord('HMX (2012-12-21 05:30:29):','大叔……',False)
    receipt = box.newrecord('Whirlpool (2012-12-21 05:31:01):','哈' * 50 + '.' * 102,True)
#    box.mark_received(receipt)
    box.newrecord('HMX (2012-12-21 05:32:00):','= =......',False)
    root.mainloop()
