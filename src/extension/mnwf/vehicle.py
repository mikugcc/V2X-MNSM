from typing import List
from subprocess import PIPE, STDOUT, Popen
from mn_wifi.net import Car, IntfWireless
from ...utils import lazy_property

class MnwfVehicle(object): 

    SPLITER = '::'

    def __init__(self, core:Car, bcst_port:int=9090) -> None:
        super().__init__()
        self.__mnwf_core:Car = core
        self.__bcst_port = bcst_port
        self.__ip: str = str(core.IP())
        self.__bcst_ip = f'{self.__ip.rpartition(".")[0]}.255'
        self._udp_package_stack: List[str] = []
        return None

    @property
    def incoming_packages_found_in_last_detect(self) -> List[str]: 
        return self._udp_package_stack.copy()

    @property
    def mesh_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[f'{self.__mnwf_core.name}-mp0']

    @property
    def wifi_intf(self) -> IntfWireless: 
        return self.__mnwf_core.wintfs[f'{self.__mnwf_core.name}-wlan1']

    @lazy_property
    def _bcster(self) -> Popen: 
        return self.__core.popen(
            ['netcat', '-ub', self.__bcst_ip, self.__bcst_port], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
    
    @lazy_property
    def _receiver(self) -> Popen: 
        return self.__core.popen(
            ['netcat', '-luk', self.__bcst_ip, self.__bcst_port],
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
    
    @lazy_property
    def mesh_sniffer(self) -> Popen: 
        return self.__core.popen(
            ['tcpdump', '-l', '-i', self.mesh_intf.name, '-A'], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )

    @lazy_property
    def wifi_sniffer(self) -> Popen: 
        return self.__core.popen(
            ['tcpdump', '-l', '-i', self.wifi_intf.name, '-A'], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )

    def broadcast(self, raw_msg: str) -> None: 
        if not raw_msg.endswith('\n'): raw_msg += '\n'
        handled_msg = f'{self.__ip}{MnwfVehicle.SPLITER}{raw_msg}'
        self._bcster.stdin.write(handled_msg)
        return None

    def detect_bcst_msgs(self) -> List[str]: 
        received_msgs: List[str] = []
        udp_packages: List[str] = []
        for package in self._tcpdump.stdout.readlines(): 
            if package is None: continue
            udp_packages.append(package)
        self._udp_package_stack = udp_packages
        for in_msg in self._bcster.stdout.readlines():
            if in_msg is None: continue
            msg_ip, _, msg_content = str(in_msg).partition(MnwfVehicle.SPLITER)
            if msg_ip == self.__ip or msg_content is None: continue
            received_msgs.append(msg_content)
        return received_msgs
