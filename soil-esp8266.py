esp.osdebug(0)
import struct, socket, network, ubinascii

from machine import Pin, ADC, deepsleep
from time import sleep

import miot, netdog


#adc = ADC(Pin(32))          # create ADC object on ADC pin
#adc.read()                  # read value, 0-4095 across voltage range 0.0v - 1.0v

## On the Adafruit board, the pin is actually labeld A2/34
adc = ADC(0) # Adafruit ADC2(labelled on board)
x = adc.read()                  
#wlan.ifconfig()         # get the interface's IP/netmask/gw/DNS addresses

print (x)

cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

av = [0] * 10
i = 0;

sampleTime = miot.Watchdog(1000*10)

led = Pin (2, Pin.OUT)

led.value(0)


rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

# check if the device woke from a deep sleep
if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from a deep sleep')

def machineDeepSleep():
    rtc.alarm(rtc.ALARM0, 1000*3600) # sleep for 1 hour
    machine.deepsleep()

def soil_data():
    global av
    return sum(av)/len(av)
    
soil_reporting_record = {
    'soil': [1,soil_data,1,60,5]
}

files = miot.make_files_hash('miot.py', 'netdog.py', 'soil-esp8266.py')

print(files)

num_msgs = 0

while True:
    v = adc.read()
    #print(v)
    i = i + 1
    av[i%10] = v
    #print (i,":",av)
    miot.tic(20)
    #netdog.tic()
    ttl = sampleTime.msecs_left()
    #print(ttl)
    if ttl <= 0:
        sampleTime.reset()
        print (i,":",av)
        if netdog.tic():
            #miot.check4updates('soil')
            miot.reporting_events(soil_reporting_record)
        num_msgs = num_msgs + 1
        #machineDeepSleep()
    sleep(0.1)



    
    



