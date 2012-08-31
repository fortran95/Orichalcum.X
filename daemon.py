# -*- coding: utf-8 -*-

# This is used to check and pull messages from given server.

import ConfigParser, sys, os, StringIO, json, shelve, hashlib, hmac, time, tkMessageBox
import notifier,processor,entity
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
    
    accounts = []
    
    accountfile = ConfigParser.ConfigParser()
    accountfile.read(os.path.join(BASEPATH,'configs','accounts.cfg'))
    
    for secname in accountfile.sections():
        accounts.append((accountfile.get(secname,'user'),
                         accountfile.get(secname,'secret'))
        
    # Start daemon, check lockfile first.
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

    # Set lock file
    f = open(LOCKFILE,'w+')
    f.close()

    clients = []
    for jid,password in accounts:
        clients.append(xmpp.XMPP(jid,password))

    # begin looping
    last_message_notify = 0
    while True:
        if not os.path.isfile(LOCKFILE):
            print "Exit the program."
            for each in clients:
                each.terminate()
                each.join()
            exit()
        else:
            f = open(LOCKFILE,'w')
            f.truncate(20)
            f.write(str(int(time.time())))
            f.close()
        # Job now.
        now = time.time()
        # Job #1: Check if clients got messages for us.

        # Job #2: Check if there is anything to send.

        # Job #3: Raise Alarm if there is any new messages.
        notify_timed = now - last_message_notify
        if notify_timed > 60:
            processor.notify()
            last_message_notify = now
        # Now All Job Done
        time.sleep(0.5)
