"""
{'info': {u'timestamp': 1346612126.0684049,
          u'xi': False,
          u'tag': u'tagged',
          'hash': '47cf6d60613e16e38db31eba35b85b4d63efd558'},
 'message': '',
 'sender': 'orxszlyzr',
 'receiver': 'orxszlyzr'
}
"""

handlers = {}

try:
    import alarming
    handlers['alarming'] = (alarming.handler,{})
except:
    print "Warning: Alarming Plugin cannot be loaded."

def plugin_do(message):
    global handlers
#    print message
    tag = message['info']['tag']

    if handlers.has_key(tag):
        handlers[tag][0](message,**handlers[tag][1])
        return True
    else:
        return False
