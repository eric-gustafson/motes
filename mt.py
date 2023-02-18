#mesh testing

import esp
import struct
import socket #UDP client broadcasts to server(s)

import network
import ubinascii

from machine import ADC
from machine import Pin, ADC
from time import sleep

import uselect

import dhcpgw



network.active(True) # esp_wifi_start
AP.config(essid='iotnet', channel=5,password='bustergus25',authmode=network.AUTH_WPA_WPA2_PSK)

dhcpgw.initIfaces(AP,STA)

print("ifconfig:")
print(AP.ifconfig())


dhcpgw.comms_up()


while True:
    dhcpgw.tic()
