import traceback
import sys
import time

def logError(e):
    """ prints a string which a human readable error text """
    print "========= % s =========" % time.asctime()
    
    # args can be empty
    if e.args:
        if len(e.args) > 1:
            print str(e.args)
        else:
            print e.args[0]
    else:
        # print exception class name
        print str(e.__class__)
    print "---------"
    print traceback.format_exc()
    print "========="
    sys.stdout.flush()
