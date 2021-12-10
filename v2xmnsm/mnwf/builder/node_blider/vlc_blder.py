from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from mn_wifi.link import WirelessLink
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Car

from .abs_node_builder import AbsNodeBuilder

class VehicleBuilder(AbsNodeBuilder): 

    def __init__(self, name:str, net: Mininet_wifi) -> None:
        super().__init__()
        self.__name: str = name
        self.__net: Mininet_wifi = net
        self.__car: Optional[Car] = None
        self.__constructor = None
        self.__params: Dict[str, Any] = {}
        self.__intfs_confs: List[Dict] = []
    
    def constructor(self, val) -> VehicleBuilder: 
        self.__constructor = val
        return self
    
    def opt_args(self, **kwargs) -> VehicleBuilder: 
        self.__params.update(kwargs)
        return self
    
    def add_intf(self, 
        ip_v4:Tuple[str, int], encrypt: str=None, 
        protocol=None, range: int = 45,
        is_link: bool=True, **kwargs
    ) -> VehicleBuilder: 
        self.__intfs_confs.append({
            'ip_v4': ip_v4,
            'range': range, 
            'encrypt': encrypt, 
            'protocol': protocol,
            'is_link': is_link,
            'parameters': kwargs
        })
        return self
    
    def build_node(self) -> Car: 
        if self.__car is None: 
            self.__car = self.__net.addCar(
                self.__name, 
                cls=self.__constructor, 
                wlans=len(self.__intfs_confs), 
                encrypt=[conf['encrypt'] for conf in self.__intfs_confs], 
                **self.__params
            )
        return self.__car
    
    def build_links(self) -> None: 
        for index, conf in enumerate(self.__intfs_confs): 
            if not conf['is_link']: continue
            params:Dict = conf['parameters']
            params['intf'] = self.__car.wintfs[index]
            self.__net.addLink(self.__car, cls=conf['protocol'], **params)
        return None
    
    def configure(self) -> None: 
        if not hasattr(self.__car, 'position'): self.__car.position = (0, 0, 0)
        for index, conf in enumerate(self.__intfs_confs):
            if 'ip_v4' not in conf: continue
            wintf: WirelessLink = self.__car.wintfs[index]
            ip_v4, prefix_len = conf['ip_v4']
            wintf.setIP(ip_v4, prefix_len)
            wintf.updateIP()
            wintf.setRange(conf['range'])
        return None
    