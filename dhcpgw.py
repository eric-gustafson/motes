#FILE: dhcpgw.py
#
# A dhcp relay agent.  This is a micropython package to
# run a dhcp relay agent on esp32 motes.

import sys, struct, utime, socket, network, uhashlib#, urequests
import uselect

DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68

sta_dhcp_client_socket = None
ap_dhcp_server_socket = None

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
    global AP, STA, poll, sta_dhcp_client_socket, ap_dhcp_server_socket
    print("dhcpgw.comms_up")    
    if (AP == None) or (STA == None):
        raise Exception("initIfaces needs to be initiated")
    ap_dhcp_server_socket = initSocket(AP, DHCP_SERVER_PORT)
    sta_dhcp_client_socket = initSocket(STA, DHCP_CLIENT_PORT)
    poll = uselect.poll()
    poll.register(sta_dhcp_client_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    poll.register(ap_dhcp_server_socket, uselect.POLLIN  | uselect.POLLHUP | uselect.POLLERR)
    return True

def comms_down():
    ## TODO: test that we don't have to unregister
    global poll, sta_dhcp_client_socket, ap_dhcp_server_socket
    print("dhcpgw.comms_down")
    poll = None
    for sock in [sta_dhcp_client_socket, ap_dhcp_server_socket]:
        sock.shutdown()
        sock.close()
    
def get_giaddr(pbuff):
    return pbuff[48:52]

#octets 48-51
      
def set_giaddr_using_straddr(packetbuff,ipaStr):
    "Set's the GIADDR part of the packet using the STA address"
    try:
        j = 0
        for i in ipaStr.split('.'):
            packetbuff[48+j]=int(i)
            j += 1
        return packetbuff
    except Execption as e:
        print("set_giaddr_using_straddr:", e)
    return None
        
def set_giaddr_using_sta_addr(packetbuff):
    "Set's the GIADDR part of the packet using the STA address"
    #octets 48-51
    global STA
    ip,nm,gw,dnss = STA.ifconfig()
    return set_giaddr_using_sta_addr(packetbuff,ip)


def incHops(pbuff):
    hi = int(pbuff[3]) #getHops(pbuff)
    hi += 1
    pbuff[3] = hi

def getHops(pbuff):
    [n] = struct.unpack("xxxb",pbuff[0:4])
    return n
    
## TODO: Send the dhcp inbound (from teh dhcpc) to the
## gateway.
##
## Should only be called when the AP is up.  We receive DHCP on the AP connection
## and unicast them to the root server.
def tic(waitTime_ms):
    global poll,sta_dhcp_client_socket, ap_dhcp_server_socket
    try:
        if poll:
            events = poll.poll(waitTime_ms)
            print ("dhcpgw.poll.events: ",events)
            for socket, flag in events:
                if flag & uselect.POLLIN:
                    buff,address = socket.recvfrom(512)
                    babuff = bytearray(buff)
                    print("DHCPGW MESSAGE:",address,"\n")
                    incHops(babuff)
                    print("hop count:",getHops(babuff))
                    set_giaddr_using_sta_addr(babuff)
                    print("giaddr:",get_giaddr(babuff))
                    buff = bytes(babuff)
                    if socket == ap_dhcp_server_socket:
                        print("root server '%s'" % (miot.RootServer))
                        sta_dhcp_client_socket.sendto(buff,(miot.RootServer,DHCP_SERVER_PORT))
                    else:
                        ap_dhcp_server_socket.sendto(buff,('255.255.255.255',DHCP_CLIENT_PORT))
    except Exception as e:
        print("dhcpgw.tic.error:",e)
