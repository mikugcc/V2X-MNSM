from __future__ import annotations
from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Tuple
from mn_wifi.link import Intf
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Node_wifi


class LinkBuilder(object): 
    
    def __init__(self, node1: Node_wifi, net: Mininet_wifi) -> None:
        super().__init__()
        self.__net: Mininet_wifi = net
        self.__link: Optional[Intf] = None
        self.__protocol = None
        self.__node1: Tuple[Optional[Node_wifi], Optional[int]] = (node1, None)
        self.__node2: Tuple[Optional[Node_wifi], Optional[int]] = (None, None)
        self.__ipv4_addr: Optional[IPv4Address] = None
        self.__parameters: Dict[str, Any] = []

    def node1(self, val:Tuple[str, int]) -> LinkBuilder:
        self.__node1 = val
        return self
    
    def node2(self, val:Tuple[str, int]) -> LinkBuilder:
        self.__node2 = val
        return self
    
    def protocol(self, val) -> LinkBuilder: 
        self.__protocol = val 
        return self
    
    def ipv4_addr(self, addr_val: str) -> LinkBuilder: 
        self.__ipv4_addr = IPv4Address(addr_val)
        return self

    def opt_args(self, **kwargs) -> LinkBuilder: 
        self.__parameters.update(kwargs)
        return self

    def build(self) -> Intf: 
        self.__link = self.__net.addLink(
            node1=self.__node1[0], port1=self.__node1[1],
            node2=self.__node2[0], port2=self.__node2[1],
            cls=self.__protocol, **self.__parameters
        )
        return self.__link

    def configure(self) -> None: 
        if self.__link is None: raise Exception('it is not allowed to configure before building')
        if self.__ipv4_addr is not None: 
            self.__link.setIP(str(self.__ipv4_addr), prefixLen=self.__ipv4_addr.max_prefixlen)
    
