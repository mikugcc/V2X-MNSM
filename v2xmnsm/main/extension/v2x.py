from typing import List
from mn_wifi.node import Car, Node_wifi
from v2xmnsm.main.extension.sumo.traffic_light import SumoTrafficLight
from v2xmnsm.main.message.cam.package import CamPackage

from .mnwf.node import MnwfNode
from .sumo.vehicle import SumoVehicle


class V2xVehicle(SumoVehicle, MnwfNode): 

    def __init__(self, 
        sm_vlc_id: str, 
        mnwf_core: Car, 
        dft_port: int = 9090
    ) -> None:
        SumoVehicle.__init__(self, sm_vlc_id)
        MnwfNode.__init__(self, mnwf_core, dft_port)
        return None

class V2xTfcLight(SumoTrafficLight, MnwfNode): 

    def __init__(self, 
        tfl_id: str, tfl_states: List[str], 
        node_wifi: Node_wifi, dft_port: int = 9090
    ) -> None:
        SumoTrafficLight.__init__(self, tfl_id, tfl_states)
        MnwfNode.__init__(self, node_wifi, dft_port)
        return None

    