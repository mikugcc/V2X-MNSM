from functools import cached_property
from queue import Queue
from subprocess import PIPE, STDOUT, Popen
from mn_wifi.node import Node_wifi
from mn_wifi.net import IntfWireless


from ...message.abs.package import Package
from ...utils import async_readlines, exec

class MnwfNode(object): 

    def __init__(self, core:Node_wifi, dft_port:int=9090) -> None:
        super().__init__()
        self.__mnwf_core:Node_wifi = core
        self.__port_num: str = str(dft_port)
        return None

    @property
    def mesh_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[0]

    @property
    def wifi_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[1]

    def __get_live_datagram_queue(self, inft:IntfWireless) -> Queue: 
        data_queue:Queue[str] = Queue()
        data_rcver = self.__mnwf_core.popen(
            [
                'tcpdump', '-l', '-A', '-i', inft.name, 
                '-n', 'udp', 'port', self.__port_num
            ],
            stdout=PIPE
        )
        async_readlines(
            into_queue=data_queue, 
            from_popen=data_rcver
        )
        return data_queue
    
    @cached_property
    def mesh_datagrams(self) -> Queue:
        '''
        The method will return a live Queue, which stored 
        the captured udp datagrams from the mesh interface. 
        The term `live` means the data in the queue will 
        update automatically when data coming.
        '''
        return self.__get_live_datagram_queue(self.mesh_intf)

    @cached_property
    def wifi_datagrams(self) -> Queue:
        '''
        The method will return a live Queue, which stored 
        the captured udp datagrams from the wifi interface. 
        The term `live` means the data in the queue will 
        update automatically when data coming.
        '''
        return self.__get_live_datagram_queue(self.wifi_intf)  

    def __get_receiver(self, intf:IntfWireless, port_num: int) -> Popen:
        return self.__mnwf_core.popen(
            [exec.UDP_RCV, f'{intf.ip.rpartition(".")[0]}.255:{port_num}'],
            stdout=PIPE, stderr=STDOUT, text=True
        )

    @cached_property
    def mesh_packages(self) -> Queue: 
        '''
        The method will return a live Queue, which stored 
        the CAM or DENM packages from the mesh interface
        The term `live` means the data in the queue will 
        update automatically when data coming.
        '''
        msg_queue: Queue[str] = Queue()
        mesh_msg_rcvr = self.__get_receiver(self.mesh_intf, self.__port_num)
        async_readlines(
            into_queue=msg_queue, 
            from_popen=mesh_msg_rcvr
        )
        return msg_queue

    @cached_property
    def wifi_packages(self) -> Queue: 
        '''
        The method will return a live Queue, which stored 
        the CAM or DENM packages from the wifi interface
        The term `live` means the data in the queue will 
        update automatically when data coming.
        '''
        msg_queue: Queue[str] = Queue()
        wifi_msg_rcvr = self.__get_receiver(self.wifi_intf, self.__port_num)
        async_readlines(
            into_queue=msg_queue, 
            from_popen=wifi_msg_rcvr
        )
        return msg_queue
    
    def __get_broadcaster(self, intf:IntfWireless, port_num: int) -> Popen: 
        to_addr = f'{intf.ip.rpartition(".")[0]}.255:{port_num}'
        return self.__mnwf_core.popen(
            [exec.UDP_SDR, intf.name, to_addr], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True
        )

    @cached_property
    def __mesh_broadcaster(self) -> Popen: 
        return self.__get_broadcaster(self.mesh_intf, self.__port_num)
    
    @cached_property
    def __wifi_broadcaster(self) -> Popen: 
        return self.__get_broadcaster(self.wifi_intf, self.__port_num)

    def __broadcast_by(self,broadcaster: Popen, package: Package) -> str: 
        if not broadcaster: return None
        handled_msg = package.to_json().replace('\n', '') + '\n'
        broadcaster.stdin.write(handled_msg)
        broadcaster.stdin.flush()
        return broadcaster.stdout.readline()

    def broadcast_by_wifi(self, package: Package) -> str: 
        return self.__broadcast_by(self.__wifi_broadcaster, package)

    def broadcast_by_mesh(self, package: Package) -> str: 
        return self.__broadcast_by(self.__mesh_broadcaster, package)
  
