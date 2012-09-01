import threading
import time
import copy
from Tkinter import *

import sleekxmpp

class XMPP(threading.Thread):
    # XMPP queue stores incoming and outgoing messages.
    # Item(s) in the queue are dict(s). Possible keys are: jid, message
    outgoing_queue = []
    incoming_queue = []
    outgoing_lock = threading.Lock()
    incoming_lock = threading.Lock()
    
    connect_status = 0   # 0-disconnected 1-connecting 2-confirm_connected,
                         # -1:error
    schedule_rec   = {'send_presence':0  ,'get_roster':0}
    schedule_set   = {'send_presence':30 ,'get_roster':30}

    def __init__(self,jid,password):
        threading.Thread.__init__(self)
        self._sig_terminate = threading.Event()

        self.xmpp = sleekxmpp.ClientXMPP(jid,password)
        self.jid = jid

        self.xmpp.add_event_handler("session_start",self._onConnected)
        self.xmpp.add_event_handler("message",self._onMessage)
        self.xmpp.add_event_handler("disconnected",self._onDisconnected)
        self.xmpp.add_event_handler("failed_auth",self._onFailedAuth)
        self.xmpp.add_event_handler("socket_error",self._onSocketError)
        

    def run(self):
        while not self._sig_terminate.isSet():
            nowtime = time.time()

            if   self.connect_status == 0:
                try:
                    self.xmpp.connect()
                    self.xmpp.process(block=False)
                    self.connect_status = 1
                except Exception,e:
                    print "XMPP deliver module: failed connecting: %s" % e
                    self.terminate()
            elif self.connect_status == 2:
                # Scheduled to send presence
                if (nowtime - self.schedule_rec['send_presence'] > 
                        self.schedule_set['send_presence']):
                    self.xmpp.sendPresence()
                    self.schedule_rec['send_presence'] = nowtime

                # Scheduled to get roster
                if (nowtime - self.schedule_rec['get_roster'] > 
                        self.schedule_set['get_roster']):
                    self.xmpp.getRoster(block=False)
                    self.schedule_rec['get_roster'] = nowtime

                # empty send queue
                self.outgoing_lock.acquire()

                while self.outgoing_queue:
                    message = self.outgoing_queue.pop(0)
                    self.xmpp.sendMessage(mto=message["jid"],
                                          mbody=message["message"],
                                          mtype="chat")

                self.outgoing_lock.release()

            time.sleep(1)

        # Exiting
        if self.connect_status == 2:
            self.xmpp.disconnect(wait=True)
        return
    def _onSocketError(self,event):
        print "Socket Error!"
        self.xmpp.disconnect(wait=False)
    def _onFailedAuth(self,event):
        print "Authentication failed"
        self.connect_status = -1
        self.terminate()

    def _onConnected(self,event):
        print "Connected"
        self.xmpp.sendPresence()
        if self.connect_status >= 0:
            self.connect_status = 2

    def _onDisconnected(self,event):
        print "Disconnected"
        if self.connect_status >= 0:
            self.connect_status = 0

    def _onMessage(self,message):
        print "Got Message"
        self.incoming_lock.acquire()
       
        if message["type"] in ("chat", "normal"):
            self.incoming_queue.append({"jid":message["from"],
                                        "message":message["body"]})

        self.incoming_lock.release()

    def setMessage(self,jid,message):
        self.outgoing_lock.acquire()
        self.outgoing_queue.append({"jid":jid,"message":message})
        self.outgoing_lock.release()
    def getMessage(self):
        self.incoming_lock.acquire()
        ret = copy.copy(self.incoming_queue)
        self.incoming_queue = []
        self.incoming_lock.release()
        return ret

    def terminate(self):
        self._sig_terminate.set()

if __name__ == '__main__':
    pwd = raw_input('password:')
    x = XMPP('neoatlantis@pidgin.su',pwd)
    x.start()
    
    while True:       
        cmd = raw_input('COMMAND: t, new, read, roster')
        if cmd == 't':
            x.terminate()
            x.join()
            del x
            exit()
        if cmd == 'new':
            receiver = 'neoatlantis@wtfismyip.com/'
            message  = raw_input('message?')
            x.setMessage(receiver,message)
        if cmd == 'roster':
            try:
                print x.xmpp.client_roster
            except:
                pass
        if cmd == 'read':
            print x.getMessage()
