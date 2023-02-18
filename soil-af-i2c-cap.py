import struct, socket, network, ubinascii

from machine import Pin, ADC, deepsleep, I2C
from time import sleep

import miot, netdog

## AdaFruit's capacitive soil sensor
##
## This program targets an esp32.

ADDR = 0x36
_TOUCH_CHANNEL_OFFSET = const(0x10)


i2c = I2C(scl=Pin(22), sda=Pin(21) , freq=100000)

 
cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

av = [0] * 10
i = 0;

sampleTime = miot.makeEveryNthSec(10)
led = Pin (2, Pin.OUT)

led.value(0)

def getSoilReading():
    buf = i2c.readfrom_mem(ADDR,_TOUCH_CHANNEL_OFFSET,2)
    return int.from_bytes(buf,'big')

reglst = i2c.scan()              # scan for slave devices
print (reglst)

while True:
    v = getSoilReading()
    #print(v)
    i = i + 1
    av[i%10] = v
    print (i,":",av)
    miot.tic(20)
    #netdog.tic()
    if sampleTime():
        print (i,":",av)
        led.value(i%2)
        if netdog.tic():
            mac = miot.wlan.config('mac')
            smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
            buf = "%s,soil,%d" % (smac, sum(av)/len(av))
            miot.sndmsg(buf)
            if miot.tic(10000):
                print ("deep sleep")
                #deepsleep(1000*4*3600)
        # print (buf)
        # [_,_,server,_] = miot.wlan.ifconfig()
        # if len(server) > 0 :
        #     print("sending to %s"%(server))
        # cs.sendto(buf, (server,3333))
        #sleep(10.0)



    
    



