# -*- coding: utf-8 -*-

# This is used to check and pull messages from given server.

import ConfigParser, sys, os, StringIO, json, shelve, hashlib, hmac, time, tkMessageBox, threading
import notifier,processor,entity,xmpp,utils
from Tkinter import *

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

class RemoteControl(object):
    def __init__(self):
        self.root = Tk()
        self.daemon = daemon()
        self._createWidgets()
        self.root.mainloop()

    def _createWidgets(self):
        
        self.powerOn = Button(text='启动进程')
        def cmdPowerOn():
            self.daemon.start()
            self.powerOn['state'] = DISABLED
            self.powerOff['state'] = NORMAL
        self.powerOn['command'] = cmdPowerOn

        self.powerOff = Button(text='停止进程')
        def cmdPowerOff():
            self.daemon.terminate()
            self.daemon.join()
            self.powerOff['state'] = DISABLED
            self.powerOn['state'] = NORMAL
        self.powerOff['state'] = DISABLED
        self.powerOff['command'] = cmdPowerOff

        self.powerOn.pack()
        self.powerOff.pack()

    
class daemon(threading.Thread):
    
    accounts = []
    clients  = []
    sig_terminate = threading.Event()

    def __init__(self):
        threading.Thread.__init__(self)
        self._read_accounts()
        for jid,password in self.accounts:
            self.clients.append([xmpp.XMPP(jid,password),[]])

    def terminate(self):
        self.sig_terminate.set()

    def _read_accounts(self):
        self.accounts = []
        accountfile = ConfigParser.ConfigParser()
        accountfile.read(os.path.join(BASEPATH,'configs','accounts.cfg'))
        for secname in accountfile.sections():
            self.accounts.append((accountfile.get(secname,'user'),
                                  accountfile.get(secname,'secret')))
    
    def run(self):
        print "Starting up XMPP clients..."
        for each in self.clients:
            each[0].start()
        print "All XMPP Clients fired."

        # begin looping
        last_message_notify = 0
        while not self.sig_terminate.isSet():
            # Job now.
            now = time.time()
    
            # Job #1: Check if clients got messages for us.
            newmessages = []
            for each in self.clients:
                if each[0].isAlive():
                    newmessages += each[0].getMessage()
            if newmessages:
                for msg in newmessages:
                    processor.handle(msg['message'],utils.stripJID(str(msg['jid'])))
                newmessages = []

            # Job #2: Check if there is anything to send.
            missions = utils.stack_get('outgoing')
            if missions:
                for mission in missions:
                    for each in self.clients:
                        if not each[0].isAlive():
                            continue
                        each[1].append(mission)
            for each in self.clients:
                if not each[1]:
                    continue
                if not each[0].isAlive():
                    continue
                if not each[0].connect_status == 2:
                    continue
                if each[0].xmpp.client_roster:
                    mission = each[1].pop(0)
                    possible_jids = entity.getJIDsByNickname(mission['receiver'])
                    if possible_jids == False:
                        continue
                    for jid in possible_jids:
                        if utils.stripJID(jid) == utils.stripJID(each[0].jid):
                            continue
                        if jid in each[0].xmpp.client_roster.keys():
                            each[0].setMessage(jid,mission['message'])     
    
            # Job #3: Raise Alarm if there is any new messages.
            notify_timed = now - last_message_notify
            if notify_timed > 60:
                processor.notify()
                last_message_notify = now
            # Now All Job Done
            time.sleep(0.5)

        print "Exit the program."
        for each in self.clients:
            each[0].terminate()
            each[0].join()
   
if __name__ == '__main__':
    rc = RemoteControl()
