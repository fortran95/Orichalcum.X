# -*- coding: utf-8 -*-

# This is used to check and pull messages from given server.

import ConfigParser, sys, os, StringIO, json, shelve, hashlib, hmac, time, tkMessageBox
import notifier,processor
from Tkinter import *

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

def find_jsonstr(retrived):
    ret_begin = retrived.find('{')
    ret_end = retrived.find('}')
    if not (ret_end > ret_begin and ret_begin >= 0):
        return False
    else:
        return retrived[ret_begin:ret_end + 1]
    
if __name__ == '__main__':
    
    accounts = {}
    
    accountfile = ConfigParser.ConfigParser()
    accountfile.read(os.path.join(BASEPATH,'configs','accounts.cfg'))
    
    for secname in accountfile.sections():
        accounts[secname] = {'user':accountfile.get(secname,'user'),
                             'secret':accountfile.get(secname,'secret')}
        
    last_message_notify = 0

    clients = []
    for nickname in 
    
    def job():
        global accounts,last_message_notify,BASEPATH

        # Job #1 List new messages
        sh = shelve.open(os.path.join(BASEPATH,"configs","orichalcum.db"),writeback=True)
        
        now = time.time()
        
        if sh.has_key('accounts') == False:
            sh['accounts'] = {}
        
        for key in accounts:
            if now - accounts[key]['lastls'] > 30:
                accounts[key]['lastls'] = now
                # VISIT THE SITE
                codes = check_messages_list(accounts[key]['host'],accounts[key]['user'],accounts[key]['secret'],accounts[key]['bits'])
                if codes != False:
                    print "Listing: %d new message(s) found." % len(codes)
                    for code in codes:
                        # Save required code.
                        if sh['accounts'].has_key(key) == False:
                            sh['accounts'][key] = {'codes':[],'messages':[]}
                        sh['accounts'][key]['codes'].append(code)
                else:
                    print codes
        # Job #2: Pull messages
        for key in accounts:
            if now - accounts[key]['lastpull'] > 30:
                accounts[key]['lastpull'] = now
                
                pulled = []
                
                if sh['accounts'].has_key(key) == False:
                    sh['accounts'][key] = {'codes':[]}
                
                for pullcode in sh['accounts'][key]['codes']:
                    print "Pulling message ID = %s ..." % pullcode
                    pm = pull_message(accounts[key]['host'],accounts[key]['user'],accounts[key]['secret'],pullcode,accounts[key]['bits'])
                    if pm != False:
                        print "(Message retrived successfully.)"
                        #  postoffice support
                        processor.handle(pm,key,accounts[key]['user']) # key is account name(not username).
                    else:
                        print "(Error in retriving message.)"
                    pulled.append(pullcode)
                
                for todel in pulled:
                    if todel in sh['accounts'][key]['codes']:
                        sh['accounts'][key]['codes'].remove(todel)
                
        notify_timed = now - last_message_notify
        if notify_timed > 60:
            processor.notify()
            last_message_notify = now                
            
        sh.close()

# Start daemon.
    LOCKFILE = os.path.join(BASEPATH,'daemonized.lock')
    if os.path.isfile(LOCKFILE):
        # See if previous daemon is running.
        f = open(LOCKFILE,'r')
        filec = f.read().strip('\x00')
        print filec
        f.close()
        try:
            if time.time() - int(filec,10) > 30:
                print "Found lock file and assumed to be dead. Will delete it."
                os.remove(LOCKFILE)
                print "Lock file deleted, wait 20 seconds for other daemon's end."
                time.sleep(20)
                if os.path.isfile(LOCKFILE):
                    exit()
            else:
                # Declare an error
                print "Error: Daemon already running."
                root = Tk()
                root.withdraw()
                if tkMessageBox.askyesno("Orichalcum", "检测到锁文件，认为 Orichalcum 后台服务可能已经启动，因此本次进程将不会启动。您可以清除锁文件然后重试，但这将导致正在运行的服务进程（如果有的话）退出。删除吗？"):
                    os.remove(LOCKFILE)
                    print "daemonized.lock REMOVED. Wait for other daemon's end."
                    time.sleep(20)
                    if os.path.isfile(LOCKFILE):
                        exit()
                else:
                    exit()
        except Exception,e:
            print "Error starting daemon:"
            print e
            exit()
    f = open(LOCKFILE,'w+')
    f.close()
    while True:
        if not os.path.isfile(LOCKFILE):
            print "Exit the program."
            exit()
        else:
            f = open(LOCKFILE,'w')
            f.truncate(20)
            f.write(str(int(time.time())))
            f.close()
        
        print ' ' * 10 + "Time to check my job."
        
        job()
        print ' ' * 10 + "My job finished."
        time.sleep(10)
