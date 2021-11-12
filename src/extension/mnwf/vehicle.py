from typing import List
from subprocess import PIPE, STDOUT, Popen
from mn_wifi.net import Car

class MnwfVehicle(object): 

    SPLITER = '::'

    def __init__(self, core:Car, bcst_ip:str=None, port:int=9090) -> None:
        super().__init__()
        self.__ip = core.IP()
        if not bcst_ip: 
            submark = self.__ip.partition(".")[0]
            bcst_ip = f'{submark}.255.255.255'
        self._bcster: Popen = core.popen(
            ['netcat', '-ub', bcst_ip, port], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
        self._receiver: Popen = core.popen(
            ['netcat', '-luk', bcst_ip, port],
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
        self._tcpdump: Popen = core.popen(
            ['tcpdump', '-l', '-i', core.intfNames()[0], '-A'], 
            stdin=PIPE, stdout=PIPE, stderr=STDOUT
        )
        self._udp_package_stack: List[str] = []

    def broadcast(self, raw_msg: str) -> None: 
        if not raw_msg.endswith('\n'): raw_msg += '\n'
        handled_msg = f'{self.__ip}{self.SPLITER}{raw_msg}'
        self._bcster.stdin.write(handled_msg)
        return None

    def detect_bcst_msg(self) -> List[str]: 
        received_msgs: List[str] = []
        udp_packages: List[str] = []
        for package in self._tcpdump.stdout.readlines(): 
            if package is None: continue
            udp_packages.append(package)
        self._udp_package_stack = udp_packages
        for in_msg in self._bcster.stdout.readlines():
            if in_msg is None: continue
            msg_ip, _, msg_content = str(in_msg).partition(self.SPLITER)
            if msg_ip == self.__ip or msg_content is None: continue
            received_msgs.append(msg_content)
        return received_msgs

    @property
    def incoming_packages_found_in_last_detect(self) -> List[str]: 
        return self._udp_package_stack.copy()

    

