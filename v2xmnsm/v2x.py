from __future__ import annotations
from typing import Dict, List, Optional, Set
from mn_wifi.node import Car, Node_wifi
from .sumo.traffic_light import SumoTrafficLight

from .mnwf import MnwfNode
from .sumo import SumoVehicle


class V2xVehicle(SumoVehicle, MnwfNode): 

    VLCS_CONTAINER: Dict[Optional[str], List[V2xVehicle]] = {None: []}

    def __init__(self, 
        sm_vlc_id: str, 
        mnwf_core: Car, 
        dft_port: int = 9090
    ) -> None:
        SumoVehicle.__init__(self, sm_vlc_id)
        MnwfNode.__init__(self, mnwf_core, dft_port)
        V2xVehicle.VLCS_CONTAINER[None].append(self)
        return None

class V2xTfcLight(SumoTrafficLight, MnwfNode): 

    def __init__(self, 
        tfl_id: str, tfl_states: List[str], 
        node_wifi: Node_wifi, dft_port: int = 9090
    ) -> None:
        SumoTrafficLight.__init__(self, tfl_id, tfl_states)
        MnwfNode.__init__(self, node_wifi, dft_port)
        return None

    