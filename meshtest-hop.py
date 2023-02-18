import esp
import struct
import socket #UDP client broadcasts to server(s)

import network
import ubinascii

from machine import ADC
from machine import Pin, ADC
from time import sleep

esp.osdebug(True)
network.ebroadcasts()


STA = network.WLAN(network.STA_IF) # create station interface
#AP = network.WLAN(network.AP_IF)
#AP.config(essid='iotnet', channel=11,password='bustergus25')

mode = network.mode()
print("wireless mode=%d"%(mode))
#network.mode(network.MODE_APSTA)
network.mode(network.MODE_STA)
print("mode=%d"%(mode))


#STA.protocol(network.MODE_11B|network.MODE_11G|network.MODE_11N|network.MODE_LR)
STA.protocol(network.MODE_LR)
#AP.protocol(network.MODE_LR);


#AP.active(True)
#STA.active(True)       # activate the interface
network.active(True) #esp_wifi_start

STA.disconnect()

#network.phy_mode(network.STA_IF) #,network.MODE_LR)
print("LR=%d" % (STA.phy_mode()))
#print("LR=%d" % (network.phy_mode(network.AP_IF)))  #,network.MODE_LR)
print (STA.phy_mode())

print(STA.ifconfig())

#adc = ADC(Pin(32))          # create ADC object on ADC pin
#adc.read()                  # read value, 0-4095 across voltage range 0.0v - 1.0v


#STA.ifconfig()         # get the interface's IP/netmask/gw/DNS addresses


mac = ""
smac = ""

cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

nets = STA.scan()
print("nets:",nets)

while True:
    if not STA.isconnected():      # check if the station is connected to an AP
        print("not connected: connecting to iotnet")
        STA.connect('iotnet', 'bustergus25') # connect to an AP
    else:
        mac = STA.config('mac')
        smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
        print (mac)
        print (smac)
        #print ("pmode=STA=%d,AP=%d"%(STA.protocol(),AP.protocol()))
        v = 9999
        buf = "%s,soil,%d" % (smac, v)
        print (buf)
        [_,_,server,_] = STA.ifconfig()
        server = '255.255.255.255'
        if len(server) > 0 :
            print("sending to %s"%(server))
        cs.sendto(buf, (server,3333))
    sleep(10.0)

    
    



