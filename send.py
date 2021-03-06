
import shelve, ConfigParser, os, sys, json
from optparse import OptionParser,OptionGroup
import xisupport,msgpack,entity,utils

def queue_message(receiver,message):
    utils.stack_set('outgoing',{'receiver':receiver,'message':message})

BASEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

op = OptionParser()

op.add_option("-i","--input",action="store",dest="input",default=False,help="Set the input file to be handled.")
op.add_option("-r","--receiver",action="store",dest="receiver",default=False,help="Specify the receiver(NICKNAME, defined in configs/alias.cfg).")
op.add_option("-t","--tag",action="store",dest="tag",default="im",help="Change message tag(default: im).")
op.add_option("-x","--xi",action="store_true", dest="usexi", default=False,help="Use xi system to encrypt. OVERRIDES user's decision in inputbox if any!")
op.add_option("-f","--flush",action="store_true",dest="omit",default=False,help="CAUTION: Omit any input, only push Xi generated messages(if any).")

(options,args) = op.parse_args()

myname  = utils.myname
recname = options.receiver
if not str(recname).strip():
    print "Please specify your intended audience by: -r/--receiver NICKNAME"
    exit()
if not (options.omit or entity.getJIDsByNickname(recname)):
    print "Unrecognized receiver nickname."
    exit()

if not options.omit:
    # Read file to get message
    if options.input == False:
        print "You must specify where to read input."
        exit()
    else:
        try:
            fp = open(options.input,'r')
            message = fp.read()
            fp.close()
        except Exception,e:
            print "File reading error: %s" % e
            exit()

# xi.postoffice support here.
if options.usexi:
    if not xisupport.XI_ENABLED:
        print "Fatal: cannot connect to Xi system."
        exit()
    if not options.omit:
        tag = json.dumps({'tag':options.tag}).encode('hex')
        xisupport.xi_queue(myname,recname,tag,message)

    handleds = xisupport.xi_handled(True)
    for p in handleds:
        try:
            tag      = json.loads(p[2].decode('hex'))
            user     = p[0] # SENDER
            receiver = p[1] # RECEIVER
            
            # BODY
            message  = msgpack.enpack(tag['tag'],p[3],True)

            queue_message(receiver,message)
        except Exception,e:
            print "Failed a letter: %s" % e
            continue
elif not options.omit:
    message = msgpack.enpack(options.tag,message,False)
    queue_message(recname,message)
