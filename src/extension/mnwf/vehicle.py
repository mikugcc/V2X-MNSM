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
        listen_ip = f'{self.mesh_intf.ip.partition(".")[0]}.255.255.255'
        mesh_msg_rcver = self.__mnwf_core.popen(
            ['udp_bcs_rcv', listen_ip, self.__port_num],
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
        async_readlines(msg_stack, mesh_msg_rcver)
        return msg_stack

    def broadcast(self, payload: str) -> None: 
        if self.__bcster is None: 
            self.mesh_intf.updateIP()
            bcst_ip = f'{self.mesh_intf.ip.rpartition(".")[0]}.255.255.255'
            self.__bcster = self.__mnwf_core.popen(
                ['udp_bcs_sdr', bcst_ip, self.__port_num], 
                stdin=PIPE, stdout=PIPE, stderr=STDOUT
            )
        encoded_package = f'{self.mesh_intf.ip}::{payload}'.encode()
        print(encoded_package, file=self.__bcster.stdin, flush=True)
        return None
