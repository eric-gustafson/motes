import esp
import struct
import socket #UDP client broadcasts to server(s)

import network
import ubinascii

from machine import ADC
from machine import Pin, ADC
from time import sleep

import uselect

#import miot

esp.osdebug(True)



# This calls: esp_wifi_init()
STA = network.WLAN(network.STA_IF) # create station interface
AP = network.WLAN(network.AP_IF)
#network.ebroadcasts()


## Set the MCU's mode to APSTA
mode = network.mode()
print("wireless mode=%d"%(mode))
network.mode(network.MODE_APSTA)
print("mode=%d"%(mode))


STA.protocol(network.MODE_11B|network.MODE_11G|network.MODE_11N|network.MODE_LR) #STA.protocol(network.MODE_LR)
AP.protocol(network.MODE_11B|network.MODE_11G|network.MODE_11N|network.MODE_LR)  #AP.protocol(network.MODE_LR);

network.active(True) # esp_wifi_start
AP.config(essid='iotnet', channel=5,password='bustergus25',authmode=network.AUTH_WPA_WPA2_PSK)

STA.disconnect()

#AP.active(True)
#STA.active(True)       # activate the interface

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

network.ebroadcasts()

cs.bind(('0.0.0.0',3333))
poll = uselect.poll()
poll.register(cs, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)


while True:
    if not STA.isconnected():      # check if the station is connected to an AP
        print("not connected")
        STA.connect('crazybird', 'bustergus25') # connect to an AP
    else:
        mac = STA.config('mac')
        smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
        print (mac)
        print (smac)
        print ("pmode=STA=%d,AP=%d"%(STA.protocol(),AP.protocol()))
        v = 9999
        buf = "%s,soil,%d" % (smac, v)
        print (buf)
        [_,_,server,_] = STA.ifconfig()
        server = '255.255.255.255'
        if len(server) > 0 :
            print("sending to %s"%(server))
        cs.sendto(buf, (server,3333))
    events = poll.poll(1000*60)
    for s, flag in events:
        if flag & uselect.POLLIN:
            buff,address = cs.recvfrom(512)
            print("message rcved:",buff,address)
            sleep(10.0)
    


    
    



