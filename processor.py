# -*- coding: utf-8 -*-
import notifier,shelve,base64,sys,os,time,hashlib,json

import plugins,xisupport,msgpack,utils,entity
from widgets.richtextbox import rich2plain

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

def handle(message,sender):
    try:
#        print message,sender
        coremessage = msgpack.depack(message)
        is_xi_message = coremessage['xi']
        entity_sender = entity.getNicknameByJID(sender)

        # put message['message'] to Xi
        tag = json.dumps({'xi':is_xi_message,
                          'tag':coremessage['tag'],
                          'timestamp':coremessage['timestamp']}).encode('hex')

        if xisupport.XI_ENABLED and is_xi_message:
            xisupport.xi_queue(entity_sender,utils.myname,tag,coremessage['message'],False)
            # Retrive Xi handled messages and parse that.
            handled = xisupport.xi_handled(False)
            for i in handled:
                handle_kernel(i[0],i[1],i[2],i[3]) # SENDER RECEIVER TAG BODY
        else:
            handle_kernel(entity_sender,utils.myname,tag,coremessage['message'])
    except Exception,e:
        print "Error handling message: %s" % e

def is_duplicate(h,timeoffset=300):
    global BASEPATH
    nowtime = time.time()
    dbname = os.path.join(BASEPATH,'cache','hashfilter.db')
    h = h.strip().lower()
    sh = shelve.open(dbname,writeback=True)

    delkeys = [k for k in sh if nowtime-sh[k] >= timeoffset]
    for delkey in delkeys:
        del sh[delkey]

    if sh.has_key(h):
        return True
    else:
        sh[h] = time.time()
        return False

def handle_kernel(sender,receiver,tag,message):
    global BASEPATH
    MSGDB_PATH0 = os.path.join(BASEPATH,'cache','msgdb.')
    try:
        tag = json.loads(tag.decode('hex'))
        tag['hash'] = hashlib.sha1(str(sender)
                                   +str(message)
                                   +str(tag['timestamp'])
                                   +str(tag['tag'])
                                  ).hexdigest()
        reconstructed = {'sender':sender,
                         'receiver':receiver,
                         'message':message,
                         'info':tag}

        # filter duplicate messages
        if is_duplicate(tag['hash']):
            return True

        # Call plugins
        if not reconstructed['info']['tag'].startswith('im_'):
            # Call related programs here !
            plugins.plugin_do(reconstructed)
            return True
        else:
            if reconstructed['info']['tag'] not in ('im_receipt',):
                quickview = rich2plain(reconstructed['message'])
                if reconstructed['info']['xi']:
                    notifier.gnotify(u'来自 %s 的机密消息' % sender, quickview)
                else:
                    notifier.gnotify(u'来自 %s 的普通消息' % sender, quickview)

        # Store message for dialogs
        while True:
            if os.path.isfile(MSGDB_PATH0 + 'lock'):
                print 'Orichalcum processor: Message database locked, waiting.'
                time.sleep(0.5)
            else:
                dblock = open(MSGDB_PATH0 + 'lock','w+')
                dblock.close()
                break

        db = shelve.open(MSGDB_PATH0 + 'db' , writeback=True)
        newhash = reconstructed['info']['hash']
        newkey = reconstructed['sender'].strip().encode('hex')

        if not db.has_key(newkey):
            db[newkey] = {newhash:reconstructed}
        else:
            db[newkey][newhash] = reconstructed

        db.close()

    except Exception,e:
        print "Error saving message: %s" % e
    # Remove database lock
    if os.path.isfile(MSGDB_PATH0 + 'lock'):
        os.remove(MSGDB_PATH0 + 'lock')
    return True

"""
def notify():
    global BASEPATH
    count = 0
    db = shelve.open(os.path.join(BASEPATH,'cache','msgdb.db'))
    for key in db:
        count += len(db[key])
    if count>0:
        notifier.osd("您有 %d 条新消息" % count)
"""
