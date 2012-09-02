import os
import sys
import shelve
import ConfigParser

import utils

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))
entitycache  = os.path.join(BASEPATH,'cache','entity.cache')
entityconfig = os.path.join(BASEPATH,'configs','alias.cfg')

if os.path.isfile(entitycache):
    cachetime = os.path.getmtime(entitycache)
else:
    cachetime = 0

if cachetime <= max(os.path.getmtime(entityconfig),
                    os.path.getmtime(os.path.realpath(sys.argv[0]))):
    print 'Generating entity cache.'

    sh = shelve.open(entitycache,writeback=True)
    sh.clear()

    cfg = ConfigParser.ConfigParser()
    cfg.read(entityconfig)
    
    for nickname in cfg.sections():
        sh[nickname] = {'special':{}, 'jids':[]}
        for x,y in cfg.items(nickname):
            x = x.strip().lower()
            if x.startswith('account'):
                sh[nickname]['jids'].append(utils.stripJID(y))
            elif x == 'allow_special':
                specials = [t.strip().lower() for t in y.split(',')]
                for special in specials:
                    if not special in ('alert','warning'):
                        continue
                    if special.startswith('*'):
                        sh[nickname]['special'][special[1:]] = True
                    else:
                        sh[nickname]['special'][special] = False
    sh.close()

def getNicknameByJID(jid):
    global entitycache
    sh = shelve.open(entitycache)
    jid = utils.stripJID(jid)
    for nickname in sh:
        if jid in sh[nickname]['jids']:
            sh.close()
            return nickname
    sh.close()
    return False

def getJIDsByNickname(nickname):
    global entitycache
    sh = shelve.open(entitycache)
    if sh.has_key(nickname):
        return sh[nickname]['jids']
    return False
