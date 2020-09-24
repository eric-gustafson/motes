#mesh testing
import esp
import struct
import socket #UDP client broadcasts to server(s)

import network
import ubinascii

from machine import ADC
from machine import Pin, ADC
from time import sleep

import uselect,usys

routes = network.routes()
print("routes:",routes)

network.route_add("172.25.18.2","255.255.255.0","172.25.18.1")
routes2 = network.routes()
print("routes2:",routes2)

if len(routes2) != (1 + len(routes) ):
    raise NameError("Failed to add a route");

network.route_add("172.25.18.2","255.255.255.0","172.25.18.1")
routes2 = network.routes()

if( len(network.routes()) != (1 + len(routes) ) ):
    raise NameErrror("Duplicate entry not blocked")

network.route_del("172.25.18.2","255.255.255.0","172.25.18.1")
routes3 = network.routes()

if len(routes3) != len(routes):
    raise NameError("Route cleanup failed");


print("r:",network.routes())


