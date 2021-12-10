from __future__ import annotations
from typing import Any, Dict, Optional
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import OVSAP

from .abs_node_builder import AbsNodeBuilder

class AccessPointBuilder(AbsNodeBuilder): 

    def __init__(self, name:str, net: Mininet_wifi) -> None:
        super().__init__()
        self.__name: str = name
        self.__net: Mininet_wifi = net
        self.__apt: Optional[OVSAP] = None
        self.__constructor = None
        self.__params: Dict[str, Any] = {}

    def constructor(self, val) -> AccessPointBuilder: 
        self.__constructor = val
        return self
    
    def opt_args(self, **kwargs) -> AccessPointBuilder: 
        self.__params.update(kwargs)
        return self
        
    def build_node(self) -> OVSAP: 
        if self.__apt is None: 
            self.__apt = self.__net.addAccessPoint(
                self.__name, cls=self.__constructor, **self.__params
            )
        return self.__apt

    def build_links(self) -> None: 
        '''WE DO NOT ADD LINK FOR AP'''
        pass
    
    def configure(self) -> None: 
        return self.__apt.start([])
        
    