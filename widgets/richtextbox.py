# -*- coding: utf-8 -*-

from Tkinter import *

class RichTextBox(Frame):
    
    def __init__(self,root,**argv):
        Frame.__init__(self,root,**argv)
        self._createWidgets()

    def _createWidgets(self):
        self.editorbar = Frame(self)
        self.textbox = Text(self)

        self.editorbar.buttons = {}
        editorbar_buttons = {'bold'     :('加粗',   {'foreground':'#F00'}),
                             'italic'   :('斜体',   {}),
                             'underline':('下划线', {'underline':True}),
                            }
        i = 0
        for key in editorbar_buttons:
            self.editorbar.buttons[key] = Button(self.editorbar,text=editorbar_buttons[key][0])
            self.textbox.tag_config(key,editorbar_buttons[key][1])
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

    def text(self):
        print SEL


if __name__ == '__main__':
    root = Tk()
    a = RichTextBox(root)
    a.grid(row=0,column=0)
    b = Button(root,text='generate')
    b.grid(row=1,column=0)
    def cmd(x=a):
        print x.text()
    b['command'] = cmd
    root.mainloop()
