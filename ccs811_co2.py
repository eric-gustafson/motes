import sys, os, struct, socket
import utime
import ujson ## config info 

import network
import ubinascii

import ssd1306
import miot,  netdog

#from machine import ADC
#from machine import Pin, ADC
from time import sleep
from machine import Pin, I2C

## Turn off/on the joining algorithm.
net = False #True
            

CCS811_ADDRESS =               0x5A

CCS811_STATUS = 0x00
CCS811_MEAS_MODE = 0x01
CCS811_ALG_RESULT_DATA = 0x02
CCS811_RAW_DATA = 0x03
CCS811_ENV_DATA = 0x05
CCS811_NTC = 0x06
CCS811_THRESHOLDS = 0x10
CCS811_BASELINE = 0x11
CCS811_HW_ID = 0x20
CCS811_HW_VERSION = 0x21
CCS811_FW_BOOT_VERSION = 0x23
CCS811_FW_APP_VERSION = 0x24
CCS811_ERROR_ID = 0xE0
CCS811_SW_RESET = 0xFF

CCS811_BOOTLOADER_APP_ERASE = 0xF1
CCS811_BOOTLOADER_APP_DATA = 0xF2
CCS811_BOOTLOADER_APP_VERIFY = 0xF3
CCS811_BOOTLOADER_APP_START = 0xF4
	
CCS811_DRIVE_MODE_IDLE = 0x00
CCS811_DRIVE_MODE_1SEC = 0x01
CCS811_DRIVE_MODE_10SEC = 0x02
CCS811_DRIVE_MODE_60SEC = 0x03
CCS811_DRIVE_MODE_250MS = 0x04
	
CCS811_HW_ID_CODE	=		0x81

CCS811_REF_RESISTOR	=		100000

#i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)

def rint8u(reg):
    ba = i2c.readfrom_mem(CCS811_ADDRESS,reg,1)
    return  int.from_bytes(ba,'big')

statfwmode = lambda stat:  stat&0x80
statappvalid = lambda stat : stat&0x10
statdr = lambda stat : stat&0x08
staterr = lambda stat : stat&0x01

def mexit(str):
    print ("Can't start CO2 app: %s" %(str))
    sleep(60)
    sys.exit(1)

reglst = i2c.scan()              # scan for slave devices

print ("scan results: ",reglst)

## swreset
i2c.writeto_mem(CCS811_ADDRESS,CCS811_SW_RESET,bytearray([0x11, 0xE5, 0x72, 0x8A]))
print ("sw reset complete")
sleep(0.2)

iid = rint8u(CCS811_HW_ID)

if iid != CCS811_HW_ID_CODE:
    print ("failed to initialize C02 sensor")
else:
    print ("co2 sensor detected")

ba = bytearray([]) 
i2c.writeto_mem(CCS811_ADDRESS, CCS811_BOOTLOADER_APP_START,ba)
sleep(0.1)
print ("read status")
sv = rint8u(CCS811_STATUS)
print ("status(%d): err=%d,data-ready=%d,app-valid=%d,fwmode=%d" %
       ( sv, staterr(sv), statdr(sv), statappvalid(sv), statfwmode(sv)))

if staterr(sv):
    mexit("status err")
    
if not statfwmode(sv):
    mexit("fwmode")

## write to the measure-mode register
##   - low pulse heating mode for measurement every 60s
##   - no interrupt
#ba = bytearray([3,0])
ba = (0x10).to_bytes(2,sys.byteorder)# bytearray([1,0])
i2c.writeto_mem(CCS811_ADDRESS,CCS811_MEAS_MODE,ba)


v = 0
#tvoc = 0

display = ssd1306.SSD1306_I2C(128, 32, i2c)
display.fill(1)  # Fill the entire display with 1="on"
display.show()
sleep(0.2)
display.fill(0)
display.show()

def handle_co2_sensor():
    global v
    sv = rint8u(CCS811_STATUS)
    mm = rint8u(CCS811_MEAS_MODE);
    errid = rint8u(CCS811_ERROR_ID)
    if sv != 152:
        print("status:",sv,",mmode:",mm,",errid:",errid)
    if statdr(sv):
        vba = i2c.readfrom_mem(CCS811_ADDRESS,CCS811_ALG_RESULT_DATA,8)
        v    = int.from_bytes(vba[0:2],'big')
        tvoc = int.from_bytes(vba[2:4],'big')
        status = int.from_bytes(vba[4:5],'big');
        error = int.from_bytes(vba[5:6],'big')
        #(vba, tvocba, status, error) = struct.unpack('2B2BBB',vba)
        #print(v,tvoc,status,error)
        displaybuff = "CO2 %d PPM" % (v)
        #print (displaybuff)
        display.fill(0)
        display.text(displaybuff, 1, 1, 1)
        display.text("uptime: " + miot.durationString(miot.uptime()),1,23,1)
        display.show()
        # if not net:
        #     print(displaybuff)
    else:
        print ("co2 sensor status - data not ready"    )

def read_co2():
    return v

co2_reporting_record = {
    'co2': [1,read_co2,1,60,5]
    }

def tick():
    global v
    v = 0
    while True:
        handle_co2_sensor()
        if net:
            miot.tic(20)
            if netdog.tic() and (v > 0):
                miot.reporting_events(co2_reporting_record)
                sleep(60)
                #mac = miot.wlan.config('mac')
                #smac = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
                #buf = "%s,co2,%d" % (smac, v)
                #print (buf)
                #miot.sndmsg(buf)
                #miot.tic(10000)
            else:
                sleep(10.0)
        else:
            sleep(10.0)

def main(argv):
    tick()

if __name__ == "__main__":
    main(sys.argv[1:])
    
    



