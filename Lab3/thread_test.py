#!/usr/bin/python
import threading
 
def starter(threadNum):
    ## Note that the arguments are passed as Strings
    print "Test Thread: %s" %(threadNum)
    return
 
threads=[]
for i in range(0,5):
    t= threading.Thread(target=starter, args=(i,))
    threads.append(t)
    t.start()