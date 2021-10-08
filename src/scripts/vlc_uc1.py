import sys
from socket import *
from ..utils.intra_vehicle import IntraVehicleCommunicator as InVlcCommunicator

if __name__ == '__main__':
    communicator = InVlcCommunicator(sys.argv[1])
    try: 
        broadcast_add = ('10.255.255.255', 8888)
        udp = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP) 
        udp.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        udp.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        udp.settimeout(0.2)
        udp.bind(broadcast_add)
        ips = {'127.0.0.1': 10}
        print('CONNECTION')
        fifo_data = communicator.data
        while(True):
            udp_bytes, from_add = udp.recvfrom(1024)
            from_ip = from_add[0]
            if(from_ip not in ips): ips[from_ip] = 10
            if(ips[from_ip] == 0): continue
            ips[from_ip] -= 1
            communicator.data = udp_bytes.decode()
            print(f'ip is: {from_ip}; \tdata is: {udp_bytes.decode()}')
            udp.sendto(udp_bytes,broadcast_add)
    except error as e:
        print(error)