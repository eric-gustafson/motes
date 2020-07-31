## FILE: netdog.py

## A application network watchdog
## The node will actively try and communicate with a command node
## on a client network.   The node will activly try and search for
## a command node to establish communications with.

## See the README.org file for more details

import sys
import utime
import network
import ujson ## config info
import miot

NetGuestTimeExpired = miot.makeEveryNthSec(60)

netscan = []
ssid = None


def leaveNet():
    global ssid
    miop.config.pop("ssid",None)
    ssid = None

def stayNet():
    global ssid
    miop.config["ssid"] = ssid
    save_config()
    
def appLock():
    val = config["ssid"]
    return isinstance(val,str) 

def nextNet():
    global netscan
    if (len(netscan) == 0):
        netscan = network.scan()
    else:
        return netscan.pop()

def dogTickIsConnected():
    """ Run the watchdog connected function.  Check if the timer to see if we should disconnect"""
    te = NetGuestTimeExpired()
    print ("time expired?:", te, ",time left:",NetGuestTimeExpired(-1)/1000)
    if te:
        miot.shutdown_comms()
        miot.wlan.disconnect()
        miot.wlan.active(False)
        miot.wlan.active(True)        
        #leaveNet()

def dogTickIsNotConnected():
    """ Advance the pointer to the next candidate """
    global netscan
    if len(netscan) == 0:
        print ("(re)scanning network")
        miot.wlan.active(False)
        miot.wlan.active(True)
        netscan = miot.wlan.scan()
    print("netscan:",netscan)
    if len(netscan) > 0:
        net = netscan.pop()
        target = net[0]
        print("attempting to connect to",target)
        miot.wlan.active(False)
        miot.wlan.active(True)                
        miot.wlan.connect(net[0],miot.config["pw"])
        NetGuestTimeExpired(True)
        ttl = NetGuestTimeExpired(-1)
        print("guest wdt:",ttl/1000)
    #miot.wlan.connect(config["ssid"], config["pw"]) # connect to an AP
    
## 
## 

def tic():
    """Called from the motes main tick loop.  Tries to reconnect on a
periodic basis, and if it fails a bunch of times it will reboot the
mote.  This function returns True if it's on the network, False if
not.

    """
    print ("netdog.tic")
    print ("miot.wlan:", miot.wlan)
    if not miot.wlan.active():
        print ("setting wlan active")
        miot.wlan.active(True)       # activate the interface
    print ("test connectivity")
    if miot.wlan.isconnected():      # check if the station is connected to an AP
        print ("is connected")
        dogTickIsConnected()
        return True
    else:
        print ("! connected")
        dogTickIsNotConnected()
        return False
    #     if NetworkWatchdogExpired():
    #         leaveNet()
    #     if( ReconnectWaitTimeExpired() ):
    #         print("connecting with %s:%s" % (miot.config["ssid"],miot.config["pw"]))
   
    #         #smac = ""
    #         #for ot in list(mac): h = hex(ot); smac += h[2] + h[3]
    #         #print(smac)
    #     return False
    # else:
    #     NetworkWatchdogExpired(watchdogTick=True)
    #     return True
    
    
# def netWatchTick():
#     ## if we are on the target network, then all is well
#     if appLock():
#         if config["ssid"] == miot.wlan.config('essid'):
#             print ("on network")
#             return True
#         if NetGuestTimeExpired()




    
