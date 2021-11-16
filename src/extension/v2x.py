from mn_wifi.node import Car

from .mnwf.vehicle import MnwfVehicle
from .sumo.vehicle import SumoVehicle


class V2xVehicle(SumoVehicle, MnwfVehicle): 

    def __init__(self, 
        sm_vlc_id: int, 
        mnwf_core: Car, 
        dft_port: int = 9090
    ) -> None:
        SumoVehicle.__init__(self, sm_vlc_id)
        MnwfVehicle.__init__(self, mnwf_core, dft_port)