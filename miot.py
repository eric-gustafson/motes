## FILE: miot.py

## Purpose: General utilities for all of the motes.  The little CPU's that are common
## to the solution who are running micropython programs.
import sys
import utime
import socket #send UDP messages server(s)
import network
import ujson ## config info
import uselect

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

def makeEveryNthSec(secs):
    "Returns a "
    last = utime.ticks_ms()
    def watcher(watchdogTick=None):
        nonlocal last
        now = utime.ticks_ms()
        if watchdogTick == None:
            if ( abs(now - last) > (1000*secs)) :
                last = now
                return True
            return False
        if watchdogTick == -1:
            return 1000*secs - abs(now - last)
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
        rcv_socket.bind(('localhost',3333))
        poll = uselect.poll()
        poll.register(rcv_socket, uselect.POLLIN)
        return True
    return False

def sndmsg(msg):
    global snd_socket,server
    if snd_socket and server:
        print("sending to %s"%(server))
        snd_socket.sendto(msg, (server,3333))        

def tic():
    """ This should be called from the main loop.  Setups of the socket to
send messages on the first invocation and receives messages on
subsequent invocations"""
    if initCommunications():
        print ("connected, checking for events")
        for events in poll.poll(20):
            print(event)
            buff,address = rcv_socket.recvfrom(512)
            print("mesg received",buff)
