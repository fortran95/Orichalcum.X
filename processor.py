# -*- coding: utf-8 -*-
import notifier,shelve,base64,sys,os,time,hashlib,json
import plugins,xisupport,msgpack,utils,entity

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

def handle(message,sender):
    try:
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

def handle_kernel(sender,receiver,tag,message):
    global BASEPATH
    MSGDB_PATH0 = os.path.join(BASEPATH,'cache','msgdb.')
    try:
        tag = json.loads(tag.decode('hex'))
        reconstructed = {'sender':sender,
                         'receiver':receiver,
                         'message':message,
                         'info':tag}

        if reconstructed['info']['tag'] != 'im':
            # Call related programs here !
            plugins.plugin_do(reconstructed)
            return True
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
        newhash = hashlib.md5(str(reconstructed['message'])
                              +str(reconstructed['info']['timestamp'])).hexdigest()
        newkey = reconstructed['sender'].strip().encode('hex')

        do_notify = False
        if db.has_key(newkey) == False:
            do_notify = True
            db[newkey] = {newhash:reconstructed}
        else:
            if not db[newkey].has_key(newhash):
                do_notify = True
                db[newkey][newhash] = reconstructed
        db.close()

        if do_notify:
            if reconstructed['info']['xi']:
                notifier.gnotify(u'来自 %s 的机密消息' % sender, '<a href="http://tieba.baidu.com">baidu.com</a>')
            else:
                notifier.gnotify(u'来自 %s 的普通消息' % sender, '<a href="http://github.com">github.com</a>')
    except Exception,e:
        print "Error saving message: %s" % e
    # Remove database lock
    if os.path.isfile(MSGDB_PATH0 + 'lock'):
        os.remove(MSGDB_PATH0 + 'lock')
    return True

def notify():
    global BASEPATH
    count = 0
    db = shelve.open(os.path.join(BASEPATH,'cache','msgdb.db'))
    for key in db:
        count += len(db[key])
    if count>0:
        notifier.osd("您有 %d 条新消息" % count)
