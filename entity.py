import os
import sys
import shelve
import ConfigParser

import utils

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))
entitycache  = os.path.join(BASEPATH,'configs','entity.cache')
entityconfig = os.path.join(BASEPATH,'configs','alias.cfg')

if os.path.isfile(entitycache):
    cachetime = os.path.getmtime(entitycache)
else:
    cachetime = 0

if cachetime <= os.path.getmtime(entityconfig):
    sh = shelve.open(entitycache,writeback=True)
    sh.clear()

    cfg = ConfigParser.ConfigParser()
    cfg.read(entityconfig)
    
    for nickname in cfg.sections():
        sh[nickname] = []
        for x,jid in cfg.items(nickname):
            sh[nickname].append(utils.stripJID(jid))

    sh.close()

def getNicknameByJID(jid):
    global entitycache
    sh = shelve.open(entitycache)
    jid = utils.stripJID(jid)
    for nickname in sh:
        if jid in sh[nickname]:
            sh.close()
            return nickname
    sh.close()
    return False

def getJIDsByNickname(nickname):
    global entitycache
    sh = shelve.open(entitycache)
    if sh.has_key(nickname):
        return sh[nickname]
    return False
