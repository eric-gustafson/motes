import sys,struct, socket, network, ubinascii

import machine
from machine import Pin, ADC, deepsleep
from time import sleep

import miot, netdog
from uModBusSerial import uModBusSerial
#from serial import Serial
#from uModBus.tcp import TCP
from network import WLAN



slave_addr=0x01
starting_address=0x00
coil_quantity=2
#starting_address=0x00
register_quantity=40
signed=False
register_values = []

uart_id = 0x02
modbus_obj = uModBusSerial(uart_id, pins=(16,17)) # 17 is tx, 16 is rx

#coil_status = modbus_obj.read_coils(slave_addr, starting_address, coil_quantity)
#print (coil_status)

#coil_status = modbus_obj.read_discrete_inputs(slave_addr, starting_address, coil_quantity)
#print (coil_status)
i = 2

#i = 255

#print (register_values[39])

toggle_cmd = 0
#if ( register_values[39] == 0 ):
#    toggle_cmd = 5

return_flag = modbus_obj.write_single_register(0x02, 39, toggle_cmd,signed)
output_flag = 'Success' if return_flag else 'Failure'

print('Writing single coil status: ' + output_flag)

#signed=True

#register_value = modbus_obj.read_holding_registers(slave_addr, starting_address, register_quantity, signed)
#print('Holding register value: ' + ' '.join('{:d}'.format(x) for x in register_value))


#coil_status = modbus_obj.read_coils(slave_addr, starting_address, coil_quantity)
#print('Coil status: ' + ' '.join('{:d}'.format(x) for x in coil_status))

mode = -1

def tick():
    global mode, register_values
    register_values = modbus_obj.read_holding_registers(0x02, 0, 80, signed)
    mode =  register_values[39]
    #print('Holding register value: ' + ' '.join('{:d}'.format(x) for x in register_value))
    print(register_values)
    #sleep(60)

def main(argv):
    tick()

if __name__ == "__main__":
    main(sys.argv[1:])
