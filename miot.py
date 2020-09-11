## FILE: miot.py

## Purpose: General utilities for all of the motes.  The little CPU's that are common
## to the solution who are running micropython programs.
import sys, struct, utime, socket, network, uhashlib, urequests
import ujson ## config info
import uselect
from time import sleep

wlan = network.WLAN(network.STA_IF) # create station interface

wlanAP = network.WLAN(network.STA_AP)

## All of the motes store their info in /c.json.  We load up the ssid
## and the password to join the network here.
config = []

try:
    if wlan.active():
        if wlan.isconnected():
            wlan.disconnect()
        wlan.active(False)
except Exception as e:
    print ("miot",str(e))
    
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


class Watchdog:
    last = None
    msecs = None

    def set_msecs(self,msecs):
        self.msecs = msecs

    def __init__(self, msecs):
        self.set_msecs(msecs)
        self.reset()

    def msecs_left(self):
        now = utime.ticks_ms()        
        return self.msecs - (now - self.last)        

    def reset(self):
        self.last =  utime.ticks_ms()
    
## Reboot the mote if we haven't been able to connect for
## an hour.
NetworkWatchdogExpired = Watchdog(3600)

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
    buf = "%s,%s,%d,%d" % (smac, tag,value, uptime())
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
                

## check the server for source code updates
## Simply download and then reboot.
def file_hash(fname):
    try:
        hasher = uhashlib.sha256()
        with open(fname, mode = "rb") as f:
            chunk = f.read(512)
            while chunk:
                hasher.update(chunk)
                chunk = f.read(512)
        return hasher.digest()
    except Exception as e:
        print("file_hash",e)
    return None

fh = {}

def make_files_hash(*files):
    global fh
    for fname in files:
        print(fname)
        value = file_hash(fname)
        print("value",value)
        if value :
            fh[fname] = value
    return fh

def hg(app,fname ,headers={}):
    global server
    try:
        url = "http://%s/%s" % (server,fname)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #log("hg.server",server)
        s.connect(socket.getaddrinfo(server, 80)[0][-1])
        cmd = (b"GET /upy/%s HTTP/1.0\r\n" %fname)
        log("hg.s",server,":",s,cmd)
        s.write(cmd)
        for k in headers:
            s.write(k)
            s.write(b": ")
            s.write(headers[k])
            s.write(b"\r\n")
        s.write(b"\r\n")            
        l = s.readline()
        log("hg.l",l)
        l = l.split(None, 2)
        status = int(l[1])
        reason = ""
        if len(l) > 2:
            reason = l[2].rstrip()
        while True:
            l = s.readline()
            if not l or l == b"\r\n":
                break
        ## We should have the content here
        with open("a", mode = "w") as f:
            chunk = s.readline()
            while chunk:
                print(chunk)
                f.write(chunk)
                chunk = s.readline() 
    except OSError:
        s.close()
        raise
        

def check4updates(app):
    try:
        for fname_key in fh:
            log("c4u.fname",fname_key)
            hg(app,fname_key)
    except Exception as e:
        print("c4u.err",e)
        

    

# def check_for_updates(files_md5_hash):
#     for f in files:
        
        
