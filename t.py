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

def initIfaces(ap,sta):
## The gateway is tied to the specific hardware/OS of the
## ESP32/FreeRTOS implementation that supports APSTA mode.
    globals AP,STA
    AP = ap
    STA = sta

def initAP():
    ## listening for dhcp client requests
    ip,nm,gw,dnss = AP.ifconfig()
    if ip:
        dhcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dhcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dhcp_server_socket.bind(ip,DHCP_SERVER_PORT)    
        
    
## This implementation is tied to the specific hardware of the esp32
## along with the APSTA mode that is provided by the esp-idf
## implementation.  We are acting as a gateway, receiving from one
## side and broadcasting to the other.

def initSockets():
    global poll, dhcp_client_socket, dhcp_server_socket
    if (AP == None) or (STA == None):
        raise Exception("initIfaces needs to be initiated")
    initAP()
    dhcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dhcp_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dhcp_client_socket.bind('0.0.0.0',DHCP_CLIENT_PORT)
    poll = uselect.poll()
    poll.register(client_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    poll.register(server_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    return True

def set_giaddr(packetbuff):
    #octets 48-51
    return packetbuff;

def tic():
    if poll:
        events = poll.poll(waitTime_ms)
        #print ("poll events: ",events)
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


