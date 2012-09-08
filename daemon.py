#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is used to check and pull messages from given server.

import ConfigParser, sys, os, StringIO, json, shelve, hashlib, hmac, time, tkMessageBox, threading
import logging
from Tkinter import *

import processor
import entity
import xmpp
import utils

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))
LOCKPATH = os.path.join(BASEPATH,'cache','daemonized.lock')
logger = logging.getLogger('orichalcumX.daemon')

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)

class RemoteControl(object):

    def __init__(self):
        self.daemon = daemon()

        self.root = Tk()
        self.root.title("Orichalcum.X 背景进程控制器")
        self.root.resizable(0,0)
        self._createWidgets()
        self.root.protocol("WM_DELETE_WINDOW", self._cmdPowerOff)
        self.root.after(0,self._watchDog)
        self.root.after(5,self.daemon.start)
        self.root.mainloop()

    def _watchDog(self):
        global LOCKPATH
        if not os.path.isfile(LOCKPATH):
            self._cmdPowerOff()

        # Feed Daemon Watchdog
        self.daemon.feedDog()

        # Report clients status
        report = ''
        for each in self.daemon.clients:
            report += '%3d.( %4d 信息待发)' % (self.daemon.clients.index(each)+1,len(each[1]))
            if each[0].isAlive:
                report += '活动'
            else:
                report += '停止'
            report += ' '
            c = each[0].connect_status
            if c == 2:
                report += '已经连接'
            elif c == 1:
                report += '连接中...'
            elif c == 0:
                report += '连接已断'
            elif c == -1:
                report += '错误中止'
            report += '\n'
        self.statusBox.config(state=NORMAL)
        self.statusBox.delete(1.0,END)
        self.statusBox.insert(END,report)
        self.statusBox.config(state=DISABLED)

        self.root.after(50,self._watchDog)
    def _cleanUp(self):
        global LOCKPATH
        try:
            self.powerOff.config(state=DISABLED)
            self.restart.config(state=DISABLED)
            self.root.update_idletasks()
            self.daemon.terminate()
            self.daemon.join()
            self.root.destroy()
            os.remove(LOCKPATH)
        except:
            pass
    def _cmdRestart(self,e=None):
        logger.debug('Commanded Restart.')

        self._cleanUp()
        restart_program()
    def _cmdPowerOff(self,e=None):
        logger.debug('Commanded PowerOff.')

        self._cleanUp()
        sys.exit()

    def _createWidgets(self):
        
        self.powerOff = Button(text='停止进程')
        self.powerOff['command'] = self._cmdPowerOff

        self.restart = Button(text='重新启动')
        self.restart['command'] = self._cmdRestart

        self.statusBox = Text(height=15,width=40)

        self.powerOff.grid(row=0,column=0)
        self.restart.grid(row=0,column=1)
        self.statusBox.grid(row=1,column=0,columnspan=2)

    
class daemon(threading.Thread):
    
    accounts = []
    clients  = []
    sig_terminate = threading.Event()

    def __init__(self):
        threading.Thread.__init__(self)
        self._read_accounts()
        for jid,password in self.accounts:
            self.clients.append([xmpp.XMPP(jid,password),[]])

    def feedDog(self):
        self.lastfeed = time.time()
    def watchDog(self):
        if time.time() - self.lastfeed > 5:
            print "Daemon Watchdog: Terminate!"
            self.terminate()

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
        logger.info("Starting up XMPP clients...")

        for each in self.clients:
            each[0].start()
        
        logger.info("All XMPP Clients fired.")
        logger.info("Feed watchdog.")
        self.feedDog()

        # begin looping
        while not self.sig_terminate.isSet():
            logger.debug("Enter a daemon running loop.")

            # Job now.
            now = time.time()
    
            # Job #1: Check if clients got messages for us.
            newmessages = []
            for each in self.clients:
                if each[0].isAlive():
                    newmessages += each[0].getMessage()
            if newmessages:
                logger.info("New message(s) retrived from clients. Will parse them.")
                for msg in newmessages:
#                    print msg
                    processor.handle(msg['message'],utils.stripJID(str(msg['jid'])))
                newmessages = []

            # Job #2: Check if there is anything to send.
            missions = utils.stack_get('outgoing')
            if missions:
                logger.info("New mission(s) accepted. Distributing them to clients.")
                for mission in missions:
                    for each in self.clients:
                        if not each[0].isAlive():
                            continue
                        each[1].append(mission)
            logger.info("Will try sending messages(if any).")
            for each in self.clients:
                if not each[1]:
                    continue
                if not each[0].isAlive():
                    logger.debug("[%s] is not alive. Will omit its job." % each[0].jid)
                    continue
                if not each[0].connect_status == 2:
                    logger.debug("[%s] is not connected(Status: %s). Will omit its job." % (each[0].jid, each[0].connect_status))
                    continue
                if each[0].xmpp.client_roster or True: # XXX This hack enables forcing each account to send.
                    mission = each[1].pop(0)
                    possible_jids = entity.getJIDsByNickname(mission['receiver'])
                    if possible_jids == False:
                        continue
                    for jid in possible_jids:
                        if utils.stripJID(jid) == utils.stripJID(each[0].jid):
                            continue
                        if jid in each[0].xmpp.client_roster.keys() or True: # The same with XXX
                            logger.debug("Set [%s] a new mission." % each[0].jid)
                            each[0].setMessage(jid,mission['message'])     
    
            # Do WatchDog
            self.watchDog()
            # Now All Job Done
            time.sleep(0.1)

        logger.info("Exit the program.")
        for each in self.clients:
            each[0].terminate()
            each[0].join(10)
            if each[0].isAlive():
                try:
                    each[0].abort()
                except:
                    pass
   
if __name__ == '__main__':
    if os.path.isfile(LOCKPATH):
        if time.time() - os.path.getmtime(LOCKPATH) > 600:
            os.remove(LOCKPATH)
            time.sleep(10)
        else:
            print 'MAKE SURE daemonized.lock HAS BEEN DELETED.'
            exit()
    open(LOCKPATH,'w').write('hello')
    rc = RemoteControl()
