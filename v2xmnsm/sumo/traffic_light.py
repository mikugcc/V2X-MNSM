from traci import trafficlight
from typing import Optional, List

class SumoTrafficLight(object): 

    def __init__(self, tfl_id: str, states: List[str]):
        self.__tfl_id = tfl_id
        self.__states = states.copy()

    @property
    def tfl_id(self) -> str:
        return self.__tfl_id

    @property
    def state(self) -> str: 
        index = trafficlight.getPhase(self.__tfl_id)
        return self.__states[index]

    @state.setter
    def state(self, val: str): 
        state_index = self.__states.index(val)
        return trafficlight.setPhase(self.__tfl_id, state_index)

    def set_state_with_duration(self, state: str, duration: Optional[int]=None) -> bool:
        try: state_index = self.__states.index(state)
        except: return False
        trafficlight.setPhaseDuration(self.__tfl_id, state_index, duration)
