import os,sys,shelve,ConfigParser
import logging

MAX_MESSAGE_LENGTH = 1024 # Changing this limit should be cautious

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

usercfg = ConfigParser.ConfigParser()
usercfg.read(os.path.join(BASEPATH,'configs','personal.cfg'))

myname  = usercfg.get('general','username').strip()

SPECIALS = ['message','notification','warning','alarm','emergency']

logging.basicConfig(
    filename    = os.path.join(BASEPATH,'cache','orichalcumX.log'),
    level       = logging.DEBUG,
    format      = '[%(asctime)-19s][%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d)\n  %(message)s\n',
    datefmt     = '%Y-%m-%d %H:%M:%S'
)

def center_window(root):
    w = root.winfo_width()
    h = root.winfo_height()
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2) # calculate position x, y
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

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
