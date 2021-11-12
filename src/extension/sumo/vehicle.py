import traci
from typing import Dict, Tuple, List

class SumoVehicle(object): 

    def __init__(self, sumo_v_id: str):
        self.__traci = traci
        self.__sumo_vlc = self.__traci.vehicle
        self.__sumo_id = sumo_v_id
        self.__duration = 0
        self.__speed_bak = 0
        self.__message_backup = {'IN': [],'OUT':[], 'TCPDUMP': []}

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
    def message_backup(self) -> Dict[str, List]: 
        return self.__message_backup

    '''
    The is a bug for the traci.vehicle.getLeader method,
    which will return None, if we change its lane during
    SUMO default lane changing behaviour. 
    '''
    def get_leader_with_distance(self) -> Tuple[str, float]: 
        out = self.__sumo_vlc.getLeader(self.__sumo_id)
        return out if out is not None else (None, None)

    def get_speed(self) -> int:
        return self.__sumo_vlc.getSpeed(self.__sumo_id)
    
    def stop(self) -> None: 
        cur_speed = self.__sumo_vlc.getSpeed(self.__sumo_id)
        if cur_speed == 0: return 
        self.__speed_bak = cur_speed
        self.__sumo_vlc.setSpeed(self.__sumo_id, 0)
    
    def restart(self)-> None: 
        if self.__speed_bak == 0: return
        self.__sumo_vlc.setSpeed(self.__sumo_id, self.__speed_bak)

    def speed(self, ex_sp)-> None: 
        self.__sumo_vlc.setSpeed(self.__sumo_id, ex_sp)

    @lane_index.setter
    def lane_index(self, value: int) -> None: 
        if self.__duration == 0: self.__duration = int(self.__traci.simulation.getTime()) + 1
        return self.__sumo_vlc.changeLane(self.__sumo_id, value, self.__duration)



        

