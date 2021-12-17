from __future__ import annotations
from typing import Dict, List, Optional, Tuple

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
        self.__pre_lane = None
        return None

    def __update_container_lane(self, new_lane) -> None: 
        V2xVehicle.VLCS_CONTAINER[self.__pre_lane].remove(self)
        if new_lane not in V2xVehicle.VLCS_CONTAINER: 
            V2xVehicle.VLCS_CONTAINER[new_lane] = []
        V2xVehicle.VLCS_CONTAINER[new_lane].append(self)

    def __get_lane(self) -> int: 
        cur_lane = SumoVehicle.lane.fget(self)
        if cur_lane != self.__pre_lane: 
            self.__update_container_lane(cur_lane)
            self.__pre_lane = cur_lane
        return cur_lane
    
    @SumoVehicle.lane.getter
    def lane(self) -> int: 
        return self.__get_lane()

    def __set_lane(self, new_lane: int) -> None: 
        pre_lane = self.lane
        if pre_lane != new_lane: 
            self.__update_container_lane(new_lane)
            self.__pre_lane = new_lane
        SumoVehicle.lane.fset(self, new_lane)
        return None
    
    @SumoVehicle.lane.setter
    def lane(self, new_lane: int) -> None: 
        return self.__set_lane(new_lane)

    def get_leader_with_distance(self) -> Tuple[str, float]:
        leader, distance = SumoVehicle.get_leader_with_distance(self)
        if leader is not None: return (leader, distance)
        lane_vlcs = V2xVehicle.VLCS_CONTAINER[self.__get_lane()]
        lane_vlcs.sort(key=lambda x:x.distance)
        next_index = lane_vlcs.index(self) + 1
        if next_index == len(lane_vlcs): return (None, None)
        leader = lane_vlcs[next_index]
        return (leader.name, leader.distance - self.distance)

    def get_possible_threads(self) -> List[str]:
        '''NEED TO BE FIX'''
        return ['car2']

class V2xTfcLight(SumoTrafficLight, MnwfNode): 

    def __init__(self, 
        tfl_id: str, tfl_states: List[str], 
        node_wifi: Node_wifi, dft_port: int = 9090
    ) -> None:
        SumoTrafficLight.__init__(self, tfl_id, tfl_states)
        MnwfNode.__init__(self, node_wifi, dft_port)
        return None

    