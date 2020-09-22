#esp.osdebug(0)
import struct, socket, network, ubinascii

from machine import Pin, ADC, deepsleep
from time import sleep

import miot, netdog, dhcpgw

miot.mesh_init()

dhcpgw.initIfaces(miot.AP,miot.STA)

av = [0] * 10
i = 0;

sampleTime = miot.Watchdog(1000*10)

led = Pin (2, Pin.OUT)

led.value(0)


def soil_data():
    global av
    return sum(av)/len(av)
    
soil_reporting_record = {
    'soil': [1,soil_data,1,60,5]
}

#files = miot.make_files_hash('miot.py', 'netdog.py', 'soil-esp8266.py')
#print(files)

num_msgs = 0

while True:
    v = 9999#adc.read()
    #print(v)
    i = i + 1
    av[i%10] = v
    #print (i,":",av)
    miot.tic(20)
    netdog.tic()
    onNet = miot.OnNet()
    if onNet > 0:
        print("on-net:", onNet)
        dhcpgw.tic(5000)
    else:
        sleep(5)
    ttl = sampleTime.msecs_left()
    print("next sample in:",ttl)
    if ttl <= 0:
        sampleTime.reset()
        print (i,":",av)
        if netdog.tic():
            #miot.check4updates('soil')
            miot.reporting_events(soil_reporting_record)
        #num_msgs += 1
    #sleep(5)








    

    


    
    



