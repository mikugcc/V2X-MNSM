from __future__ import annotations
from typing import Dict, Any
from mn_wifi.net import Mininet_wifi

from v2xmnsm.mnwf.builder.node_blider.tfl_blder import TrafficLightBuilder

from .node_blider.abs_node_builder import AbsNodeBuilder
from .node_blider.vlc_blder import VehicleBuilder
from .node_blider.apt_blder import AccessPointBuilder

class NetBuilder(object): 

    def __init__(self, link, wmediumd_mode, **kwargs) -> None:
        super().__init__()
        self.__propagation_model: Dict[str, Any] = {}
        self.__node_builders: Dict[str, AbsNodeBuilder] = {}
        self.__net = Mininet_wifi(link=link, wmediumd_mode=wmediumd_mode, **kwargs)
    
    def propagation_model(self, **kwargs) -> NetBuilder: 
        self.__propagation_model.update(kwargs)

    def new_car(self, car_name: str) -> VehicleBuilder: 
        node_key = f'{VehicleBuilder.__name__}.{car_name}'
        if node_key not in self.__node_builders: 
            self.__node_builders[node_key] = VehicleBuilder(car_name, self.__net)
        return self.__node_builders[node_key]
    
    def new_traffic_light(self, tfl_name: str) -> TrafficLightBuilder:
        node_key = f'{TrafficLightBuilder.__name__}.{tfl_name}'
        if node_key not in self.__node_builders: 
            self.__node_builders[node_key] = TrafficLightBuilder(tfl_name, self.__net)
        return self.__node_builders[node_key]

    def new_access_point(self, apt_name: str) -> AccessPointBuilder: 
        node_key = f'{AccessPointBuilder.__name__}.{apt_name}'
        if node_key not in self.__node_builders: 
            self.__node_builders[node_key] = AccessPointBuilder(apt_name, self.__net)
        return self.__node_builders[node_key]
    
    def build(self) -> Mininet_wifi:
        for node_blder in self.__node_builders.values(): 
            node_blder.build_node()
        self.__net.setPropagationModel(**self.__propagation_model)
        self.__net.configureWifiNodes()
        for node_blder in self.__node_builders.values(): 
            node_blder.build_links()
        self.__net.build()
        for node_blder in self.__node_builders.values(): 
            node_blder.configure()
        return self.__net
