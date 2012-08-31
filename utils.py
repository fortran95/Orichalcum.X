import os,sys,shelve
BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

usercfg = ConfigParser.ConfigParser()
usercfg.read(os.path.join(BASEPATH,'configs','personal.cfg'))

myname  = usercfg.get('general','username').strip()


def stripJID(jid):
    if '/' in jid:
        jid = jid.split('/',1)[0]
    return jid.strip()

def stack_set(stackname,value):
    global BASEPATH
    stackpath = os.path.join(BASEPATH,'cache','stack')
    sh = shelve.open(stackpath,writeback=True)
    if not sh.has_key(stackname):
        sh[stackname] = []
    sh[stackname].append(value)

def stack_get(stackname):
    global BASEPATH
    stackpath = os.path.join(BASEPATH,'cache','stack')
    sh = shelve.open(stackpath,writeback=True)
    ret = False
    if sh.has_key(stackname):
        ret = sh[stackname][:]
        sh[stackname] = []
    sh.close()
    return ret
