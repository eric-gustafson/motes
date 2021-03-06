import struct
import socket #UDP client broadcasts to server(s)

import network
import ubinascii

from machine import ADC
from machine import Pin, ADC
from time import sleep



wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

#adc = ADC(Pin(32))          # create ADC object on ADC pin
#adc.read()                  # read value, 0-4095 across voltage range 0.0v - 1.0v

## On the Adafruit board, the pin is actually labeld A2/34
adc = ADC(Pin(34)) # Adafruit ADC2(labelled on board)
adc.atten(ADC.ATTN_11DB)    # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
adc.width(ADC.WIDTH_12BIT)   # set 9 bit return values (returned range 0-511)
adc.read()                  
#wlan.ifconfig()         # get the interface's IP/netmask/gw/DNS addresses


mac = ""
smac = ""

cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

while True:
    v = adc.read()
    print(v)
    if not wlan.isconnected():      # check if the station is connected to an AP
        print("not connected")
        wlan.connect('crazybird', 'bustergus25') # connect to an AP
        #smac = ""
        #for ot in list(mac): h = hex(ot); smac += h[2] + h[3]
        #print(smac) 
    else:
        mac = wlan.config('mac')
        smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
        print (mac)
        print (smac)
        buf = "%s,soil,%d" % (smac, v)
        print (buf)
        [_,_,server,_] = wlan.ifconfig()
        if len(server) > 0 :
            print("sending to %s"%(server))
        cs.sendto(buf, (server,3333))
    sleep(60.0)

    
    



