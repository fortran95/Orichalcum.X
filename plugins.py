"""
{'timestamp': 1346572318.0377929, 'message': '', 'tag': u'tagged', 'more': {u'timestamp': 1346572318.0377929, u'tag': u'tagged'}}
"""

handlers = {}

try:
    import akasha
    handlers['akasha'] = (akasha.handler,{'keep-record':False})
except:
    print "Warning: Akasha cannot be loaded."

def plugin_do(message):
    global handlers
    print message
    tag = message['tag']

    if handlers.has_key(tag):
        handlers[tag][0](message,handlers[tag][1])
        return True
    else:
        return False
