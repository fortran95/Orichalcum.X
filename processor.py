# -*- coding: utf-8 -*-
import notifier,shelve,base64,sys,os,time,hashlib,json
import plugins,xisupport,msgpack,utils,entity

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

def parse(message,moretags,sender):
    # If this is a marked message(with tags. only tag='im' will be shown, others will be transfered to related programs.
    tag=''
    try:
        moretags = json.loads(moretags.decode('hex'))
        timestamp = moretags['timestamp']
        tag = moretags['tag']
    except:
        tag = 'im'
    return {'tag':tag,'message':message,'more':moretags,'timestamp':timestamp}
def handle(message,sender):
    try:
        coremessage = msgpack.depack(message)
        is_xi_message = coremessage['xi']
        entity_sender = entity.getNicknameByJID(sender)

        # put message['message'] to Xi
        tag = json.dumps({'tag':coremessage['tag'],'timestamp':coremessage['timestamp']}).encode('hex')

        if xisupport.XI_ENABLED and is_xi_message:
            xisupport.xi_queue(entity_sender,utils.myname,tag,coremessage['message'],False)
            # Retrive Xi handled messages and parse that.
            handled = xisupport.xi_handled(False)
            for i in handled:
                handle_kernel(i[0],i[1],i[2],i[3],True) # SENDER RECEIVER TAG BODY
        else:
            handle_kernel(entity_sender,utils.myname,tag,coremessage['message'],False)
    except Exception,e:
        print "Error handling message: %s" % e

def handle_kernel(sender,receiver,tag,message,isxi):
    global BASEPATH
    MSGDB_PATH0 = os.path.join(BASEPATH,'configs','msgdb.')
    try:
        guidance = parse(message,tag,sender)    # Mix rubbish up. Poor design.
        tag = guidance['more']

        if guidance['tag'] != 'im':
            # Call related programs here !
            plugins.plugin_do(guidance)
            return True
        else:
            message = guidance['message']
        # Store message
        #notifier.showMessage(message['sender'],message['message'])
        while True:
            if os.path.isfile(MSGDB_PATH0 + 'lock'):
                print 'Orichalcum processor: Message database locked, waiting.'
                time.sleep(0.5)
            else:
                dblock = open(MSGDB_PATH0 + 'lock','w+')
                dblock.close()
                break
        
        db = shelve.open(MSGDB_PATH0 + 'db' , writeback=True)
        newpiece = {'message':message,'timestamp':guidance['timestamp'],'xi':isxi}
        newhash = base64.encodestring(hashlib.md5(message + guidance['timestamp']).digest()).strip()
        newkey = base64.encodestring(sender)
        if db.has_key(newkey) == False:
            db[newkey] = {newhash:newpiece}
        else:
            db[newkey][newhash] = newpiece
        db.close()

        if isxi:
            notifier.gnotify('来自 %s 的机密消息' % sender,message)
        else:
            notifier.gnotify('来自 %s 的普通消息' % sender, message)
    except Exception,e:
        print "Error saving message: %s" % e
    # Remove database lock
    if os.path.isfile(MSGDB_PATH0 + 'lock'):
        os.remove(MSGDB_PATH0 + 'lock')
    return True

def notify():
    global BASEPATH
    count = 0
    db = shelve.open(os.path.join(BASEPATH,'configs','msgdb.db'))
    for key in db:
        count += len(db[key])
    if count>0:
        notifier.osd("您有 %d 条新消息" % count)
