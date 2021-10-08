import sys
import time
from socket import *

if __name__ == '__main__':
    try: 
        broadcast_add = ('10.255.255.255', 8888)
        udp = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP) 
        udp.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        udp.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        udp.settimeout(0.2)
        counter = 0
        while(counter != 1000):
            msg_bytes = bytes(sys.argv[1], 'utf-8')
            udp.sendto(msg_bytes, broadcast_add)
            print(f'THIS IS {counter} MSG')
            counter += 1
            time.sleep(1)
    except OSError as e:
        print(f'ERROR: {e}')