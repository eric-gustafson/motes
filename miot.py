## FILE: miot.py

## Purpose: General utilities for all of the motes.  The little CPU's that are common
## to the solution who are running micropython programs.
import sys
import utime
import network
import ujson ## config info

wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

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
        else:
            last = now
            return True
    return watcher

## Try and reconnect every n seconds
ReconnectWaitTimeExpired = makeEveryNthSec(60)

## Reboot the mote if we haven't been able to connect for
## an hour.
NetworkWatchdogExpired = makeEveryNthSec(3600)

## All of the motes store their info in /c.json.  We load up the ssid
## and the password to join the network here.
ssid = "ssid"
pw = "pw"

try:
    with open('/c.json','r') as f:
        config = ujson.load(f)
        ssid = config["ssid"]
        pw = config["pw"]
except Exception as e:
    print ("couldn't process config file: %s",str(e))

## Called from the motes main tick loop.  Tries to reconnect
## on a periodic basis, and if it fails a bunch of times it will
## reboot the mote.
## This function returns True if it's on the network, False if not.
def networkTick():
    global ssid
    global pw
    global wlan
    if not wlan.isconnected():      # check if the station is connected to an AP
        if NetworkWatchdogExpired():
            sys.exit(2)
        if( ReconnectWaitTimeExpired() ):
            print("connecting with %s:%s" % (ssid,pw))
            wlan.connect(ssid, pw) # connect to an AP
            #smac = ""
            #for ot in list(mac): h = hex(ot); smac += h[2] + h[3]
            #print(smac)
        return False
    else:
        NetworkWatchdogExpired(watchdogTick=True)
        return True


