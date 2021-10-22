from typing import Tuple, List
import traci

class VlcControlUtil(object): 

    SUMO_Traci = traci

    def __init__(self, sumo_v_id: str):
        self.__traci = traci
        self.__sumo_vlc = self.__traci.vehicle
        self.__sumo_id = str(sumo_v_id)
        self.__duration = 0
        self.__message_backup = []

    @property
    def position(self) -> Tuple: 
        x,y = self.__sumo_vlc.getPosition(self.__sumo_id)
        return (x, y, 0)
    
    @property
    def lane_index(self) -> int: 
        return self.__sumo_vlc.getLaneIndex(self.__sumo_id) 

    @property
    def distance(self) -> int: 
        return self.__sumo_vlc.getDistance(self.__sumo_id) 
    
    @property
    def name(self) -> int: 
        return self.__sumo_id

    @property
    def message_backup(self) -> List: 
        return self.__message_backup

    '''
    The is a bug for the traci.vehicle.getLeader method,
    which will return None, if we change its lane during
    SUMO default lane changing behaviour. 
    '''
    def get_leader_with_distance(self) -> Tuple[str, float]: 
        out = self.__sumo_vlc.getLeader(self.__sumo_id)
        return out if out is not None else (None, None)
    
    def stop(self) -> None: 
        self.__sumo_vlc.setSpeed(self.__sumo_id, 0)
    
    @lane_index.setter
    def lane_index(self, value: int) -> None: 
        if self.__duration == 0: self.__duration = int(self.__traci.simulation.getTime()) + 1
        return self.__sumo_vlc.changeLane(self.__sumo_id, value, self.__duration)



        

