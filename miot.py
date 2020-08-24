## FILE: miot.py

## Purpose: General utilities for all of the motes.  The little CPU's that are common
## to the solution who are running micropython programs.
import sys, struct, utime, socket, network
import ujson ## config info
import uselect
from time import sleep

wlan = network.WLAN(network.STA_IF) # create station interface

## All of the motes store their info in /c.json.  We load up the ssid
## and the password to join the network here.
config = []

if wlan.active():
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(False)

init_time = 0

def uptime ():
    global init_time
    if init_time == 0:
        init_time = utime.ticks_ms()
    return utime.ticks_ms() - init_time

def uptime_s():
    return uptime()/1000

def log (*args):
    newargs = tuple([uptime_s(),":"]) + args
    print(*newargs)

def makeEveryNthSec(secs):
    "Returns a "
    last = utime.ticks_ms()
    def watcher(watchdogTick=None):
        nonlocal last,secs
        now = utime.ticks_ms()
        if watchdogTick == None:
            if ( abs(now - last) > (1000*secs)) :
                last = now
                return True
            return False
        if watchdogTick == -1:
            return 1000*secs - abs(now - last)
        if isinstance(watchdogTick,int):
            secs = watchdogTick
        else:
            last = now
            return True
    return watcher

## Try and reconnect every n seconds
ReconnectWaitTimeExpired = makeEveryNthSec(60)

## Reboot the mote if we haven't been able to connect for
## an hour.
NetworkWatchdogExpired = makeEveryNthSec(300)

def load_config():
    global config
    try:
        with open('/c.json','r') as f:
            config = ujson.load(f)
    except Exception as e:
        print ("couldn't process config file: %s",str(e))

def save_config():
    global config
    try:
        with open('/c.json','w') as f:
            ujson.dump(config,f)
    except Exception as e:
        print ("couldn't save config file: %s",str(e))

    
load_config()
        
def durationString(us_duration):
    s = us_duration/1000
    str = "%ds" % (s)
    return str

#cs = None
poll = None
server = None

snd_socket = None
rcv_socket = None

def shutdown_comms():
    """When the mote switches networks, it should shutdown the sockets and
then bring them back up when a new home is found.

    """
    global snd_socket, rcv_socket
    if snd_socket:
        snd_socket.close()
        snd_socket = None
    if rcv_socket:
        rcv_socket.close()
        rcv_socket = None

def initCommunications():
    global poll,server,snd_socket,rcv_socket
    if wlan.active() and wlan.isconnected() and not snd_socket:
        snd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rcv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        snd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
        rcv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        [_,_,server,_] = wlan.ifconfig()
        ## No bind on the sending socket
        #snd_socket.bind((server,3333))
        rcv_socket.bind(('0.0.0.0',3333))
        poll = uselect.poll()
        poll.register(rcv_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
        return True
    return False

def sndmsg(msg):
    global snd_socket,server
    if snd_socket and server:
        log("sending to %s"%(server))
        snd_socket.sendto(msg, (server,3333))        

msgHooks = []

def addHook(thunk):
    ##pushnew
    if not thunk in msgHooks:
        msgHooks.append(thunk)

def distributeMsgToListeners(msg):
    for e in msgHooks:
        try:
            e(msg)
        except Exception as e:
            print(e)

def logMsg(buff):
    print("processing msg:",buff)


    
def tic(waitTime_ms):
    """ This should be called from the main loop.  Setups of the socket to
send messages on the first invocation and receives messages on
subsequent invocations"""
    global poll, rcv_socket
    initCommunications()
    addHook(logMsg)
    #print("hooks:",msgHooks)
    if poll:
        #print ("connected, checking for events")
        events = poll.poll(waitTime_ms)
        #print ("poll events: ",events)
        for s, flag in events:
            if flag & uselect.POLLIN:
                buff,address = rcv_socket.recvfrom(512)
                distributeMsgToListeners(buff)
                sleep(waitTime_ms/1000)
                return True
    return False

def snd_reporting_event(tag,value):
    global wlan
    mac = wlan.config('mac')
    smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
    buf = "%s,%s,%d" % (smac, tag,value)
    sndmsg(buf)

## We remember the last reading we sent, along with the time.
reporting_memory = {}

def reporting_events(reporting_record):
    global reporting_memory
    for tag_key in reporting_record:
        handle, thunk, min_reporting_time, max_reporting_time, value_delta = reporting_record[tag_key]
        new_value = thunk()
        now = uptime_s()
        if handle in reporting_memory:
            last, tls  = reporting_memory[handle]
            time_delta = abs(now - tls)
            ## We are above the minimum reporting time, and we've exceeded our firing threshold
            if ( abs(last-new_value) > value_delta )  and ( time_delta > min_reporting_time ) :
                snd_reporting_event(tag_key,new_value)
                reporting_memory[handle] = [new_value, now]
            ## We've gone over the max reporting time
            if time_delta > max_reporting_time:
                snd_reporting_event(tag_key,new_value)
                reporting_memory[handle] = [new_value, now]                
        else:
            snd_reporting_event(tag_key,new_value)
            reporting_memory[handle] = [new_value, now]        
                
    

