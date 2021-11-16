from mn_wifi.net import Car, IntfWireless
from functools import cached_property
from utils import async_readlines
from subprocess import PIPE, STDOUT, Popen
from typing import Optional, List

class MnwfVehicle(object): 

    def __init__(self, core:Car, dft_port:int=9090) -> None:
        super().__init__()
        self.__mnwf_core:Car = core
        self.__port_num: str = str(dft_port)
        self.__bcster: Optional[Popen] = None
        return None

    @property
    def mesh_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[0]

    @property
    def wifi_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[1]

    def __get_live_datagram_stack(self, inft_name:str) -> List[str]: 
        data_stack:List[str] = []
        data_rcver = self.__mnwf_core.popen(
            ['tcpdump', '-l', '-i', inft_name, '-A'], 
            stdout=PIPE
        )
        async_readlines(data_stack, data_rcver)
        return data_stack
    
    @cached_property
    def mesh_datagram_stack(self) -> List[str]:
        return self.__get_live_datagram_stack(self.mesh_intf.name)

    @cached_property
    def wifi_datagram_stack(self) -> List[str]:
        return self.__get_live_datagram_stack(self.wifi_intf.name)        

    @cached_property
    def received_bcst_stack(self) -> List[str]: 
        msg_stack: List[str] = []
        self.mesh_intf.updateIP()
        to_address = f'{self.mesh_intf.ip.partition(".")[0]}.255.255.255:{self.__port_num}'
        mesh_msg_rcver = self.__mnwf_core.popen(
            ['udp_bcs_rcv', to_address],
            stdout=PIPE, stderr=STDOUT, text=True
        )
        async_readlines(msg_stack, mesh_msg_rcver)
        return msg_stack
    
    def __get_broadcaster(self, intf:IntfWireless, port_num: int) -> Popen: 
        intf.updateIP()
        to_addr = f'{intf.ip.partition(".")[0]}.255.255.255:{port_num}'
        return self.__mnwf_core.popen(
            ['udp_bcs_sdr', intf.name, to_addr], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True
        )

    @cached_property
    def __mesh_broadcaster(self) -> Popen: 
        return self.__get_broadcaster(self.mesh_intf, self.__port_num)
    
    @cached_property
    def __wifi_broadcaster(self) -> Popen: 
        return self.__get_broadcaster(self.wifi_intf, self.__port_num)


    def broadcast_by_wifi(self, payload: str) -> str: 
        self.__mesh_broadcaster.stdin.write(f'{payload}\n')
        self.__mesh_broadcaster.stdin.flush()
        return self.__mesh_broadcaster.stdout.readline()

    def broadcast_by_mesh(self, payload: str) -> str: 
        self.__wifi_broadcaster.stdin.write(f'{payload}\n')
        self.__wifi_broadcaster.stdin.flush()
        return self.__wifi_broadcaster.stdout.readline()
