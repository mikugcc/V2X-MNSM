from mn_wifi.node import Car
from typing import Tuple
import abc, traci

class VlcControlUtil(metaclass=abc.ABCMeta): 

    def __init__(self, sumo_v_id: int):
        self.__sumo_vlc = traci.vehicle
        self.__sumo_id = str(sumo_v_id)
        self.__duration = 0

    @property
    def position(self) -> Tuple: 
        x,y = self.__sumo_vlc.getPosition(self.__sumo_id)
        return (x, y, 0)
    
    @property
    def lane_index(self) -> int: 
        return self.__sumo_vlc.getLaneIndex(self.__sumo_id) 
    
    @lane_index.setter
    def lane_index(self, value: int) -> None: 
        if self.__duration == 0: self.__duration = traci.simulation.getTime() + 1
        return self.__sumo_vlc.changeLane(self.__sumo_id, value, self.__duration)



        

