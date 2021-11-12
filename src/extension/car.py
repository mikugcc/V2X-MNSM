from typing import Optional
from .mnwf.vehicle import MnwfVehicle
from .sumo.vehicle import SumoVehicle
from .sumo.controller import SumoStepListener, SumoControlThread

class CarController(SumoStepListener): 

    def __init__(self, sm_vlc: SumoVehicle, mn_vlc: MnwfVehicle) -> None:
        super().__init__()
        self._sm_vlc = sm_vlc
        self._mn_vlc = mn_vlc

    
    






