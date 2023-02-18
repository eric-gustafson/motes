## FILE: netdog.py

## A application network watchdog
## The node will actively try and communicate with a command node
## on a client network.   The node will activly try and search for
## a command node to establish communications with.

## See the README.org file for more details

import machine, sys,utime
import network
import ujson ## config info
import miot
from time import sleep

NetWD = miot.Watchdog(60*1000)
RebootWD = miot.Watchdog(1000*15*60)

netscan = []
ssid = None


# def leaveNet():
#     global ssid
#     miop.config.pop("ssid",None)
#     ssid = None

# def stayNet():
#     global ssid
#     miop.config["ssid"] = ssid
#     save_config()
    
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
    tl = NetWD.msecs_left()
    print ("network-watchdog-timer:", tl)
    if tl <= 0:
        miot.comms_down()
        network.active(False)
        network.active(True)
        miot.STA.disconnect()
        #leaveNet()

def dogTickIsNotConnected():
    """ Advance the pointer to the next candidate """
    global netscan
    if len(netscan) == 0:
        print ("(re)scanning network")
        network.active(False)
        network.active(True)
        miot.STA.disconnect()        
        netscan = miot.STA.scan()
        netscan.reverse()
    print("netscan:",netscan)
    if len(netscan) > 0:
        net = netscan.pop()
        target = net[0]
        #arget = b'airia1'
        pw = miot.config["pw"]
        print("attempting to connect to",target,pw)
        miot.STA.connect(target,pw)
        NetWD.reset()
        ttl = NetWD.msecs_left()
        print("guest wdt:",ttl/1000)
        i = 0;
        while not miot.STA.isconnected() and i < 30: 
            #print("! connected",i)
            i = i + 1
            sleep(1)
        print("is connected:",miot.STA.isconnected(),":",target)
    #miot.STA.connect(config["ssid"], config["pw"]) # connect to an AP
    
## 
## 
def networkHeartBeat(messg,addr):
    global RebootWD,NetWD
    msg = messg.decode('utf-8')
    a,b,*rest = msg.split()
    ip,port = addr
    if a == u'stay':
        print("network watchdog received:", b)
        miot.RootServer = ip
        RebootWD.reset()
        NetWD.set_msecs(1000*int(b))
        NetWD.reset()
        if miot.OnNet() == 0:
            miot.ap_up()
    else:
        print("networkHeartBeat:",messg)

def init():
    #print("initializing netdog")
    miot.addHook(networkHeartBeat)
        
def tic():
    """Called from the motes main tick loop.  Tries to reconnect on a
periodic basis, and if it fails a bunch of times it will reboot the
mote.  This function returns True if it's on the network, False if
not.
    """
    print("netdog.tic:root=", miot.RootServer, ",STA=",miot.STA, ",AP=",miot.STA.ifconfig())
    onNet =  miot.OnNet()
    init()
    delta =  RebootWD.msecs_left()
    if ( delta <= 0 ):
        print("Initiation machine reboot, too long to connect")
        machine.reset()
    print("Timers: reboot=",delta,",on-net=", onNet)
    if miot.STA.isconnected():      # check if the station is connected to an AP
        #print ("connected")
        dogTickIsConnected()
        return True
    else:
        print ("!connected")
        dogTickIsNotConnected()
        return False
    #     if NetworkWatchdogExpired.tic():
    #         leaveNet()
    #     if( ReconnectWaitTimeExpired() ):
    #         print("connecting with %s:%s" % (miot.config["ssid"],miot.config["pw"]))
   
    #         #smac = ""
    #         #for ot in list(mac): h = hex(ot); smac += h[2] + h[3]
    #         #print(smac)
    #     return False
    # else:
    #     NetworkWatchdogExpiredo(watchdogTick=True)
    #     return True
    
    
# def netWatchTick():
#     ## if we are on the target network, then all is well
#     if appLock():
#         if config["ssid"] == miot.STA.config('essid'):
#             print ("on network")
#             return True
#         if NetWD()




    
