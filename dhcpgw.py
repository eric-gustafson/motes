#FILE: dhcpgw.py
#
# A dhcp relay agent.  This is a micropython package to
# run a dhcp relay agent on esp32 motes.

import sys, struct, utime, socket, network, uhashlib#, urequests
import uselect

DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68

dhcp_client_socket = None
dhcp_server_socket = None

poll = None

## WLAN objects from micropython's network package
AP = None
STA = None

## The number of hops away from the aggregator.  This will be placed
## in the dhcp message.  The EM will use this information to make
## decisions on who to add the node through
nhops = None

## The gateway is tied to the specific hardware/OS of the
## ESP32/FreeRTOS implementation that supports APSTA mode.
def initIfaces(ap,sta):
    global AP,STA
    AP = ap
    STA = sta

def initSocket(IFACE, PORT):
    ip,nm,gw,dnss = IFACE.ifconfig()
    ## listening for dhcp client requests
    if ip:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip,PORT))
        return sock
    raise Exception("Interface lacks an IP address")
    
## This implementation is tied to the specific hardware of the esp32
## along with the APSTA mode that is provided by the esp-idf
## implementation.  We are acting as a gateway, receiving from one
## side and broadcasting to the other.

def comms_up():
    global poll, dhcp_client_socket, dhcp_server_socket
    print("dhcpgw.comms_up")    
    if (AP == None) or (STA == None):
        raise Exception("initIfaces needs to be initiated")
    dhcp_server_socket = initSocket(AP, DHCP_SERVER_PORT)
    dhcp_client_socket = initSocket(STA, DHCP_CLIENT_PORT)
    poll = uselect.poll()
    poll.register(dhcp_client_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    poll.register(dhcp_server_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    return True

def comms_down():
    ## TODO: test that we don't have to unregister
    print("dhcpgw.comms_down")
    poll = None
    for sock in [dhcp_client_socket, dhcp_server_socket]:
        sock.shutdown()
        sock.close()
    

def set_giaddr(packetbuff):
    #octets 48-51
    return packetbuff;

## TODO: Send the dhcp inbound (from teh dhcpc) to the
## gateway.
##
## Should only be called when the AP is up.  We receive DHCP on the AP connection
## and unicast them to the root server.
def tic(waitTime_ms):
    if poll:
        events = poll.poll(waitTime_ms)
        print ("dhcpgw.poll.events: ",events)
        for socket, flag in events:
            if flag & uselect.POLLIN:
                buff,address = socket.recvfrom(512)
                print("address:",address)
                print("check the address. if 255.255.255.255 the forward to the other interface")
                forward_packet(buff,toaddress)
                op,htype,hlen,hops = buff
                buff[3] = 1 + hops
                if socket == dhcp_server_socket:
                    dhcp_client_socket.sendto(buff,('255.255.255.255',DHCP_CLIENT_PORT))
                else:
                    dhcp_server_socket.sendto(buff,('255.255.255.255',DHCP_SERVER_SOCKET))
