from typing import Tuple
from random import random
from dataclasses import asdict, dataclass
from src.message.abs.body import Body

@dataclass(frozen=True)
class __Station_Characteristics: 
    mobile_its_station: bool = False # ITS station which we did not implement
    private_its_station: bool = False # we also did not implement sequenct id
    physical_relevant_its_station: bool = False # we also did not implement sequenct id

@dataclass(frozen=True)
class __Reference_Position: 
    lane: str # NOT IN ORIGIN DENM BUT WE ADDED IT HERE
    position: Tuple[int, int]
    elevation: int = 0
    heading: int = 0

class CamBody(Body): 
    def __init__(self, lane: str, leader: str, speed: int, position: Tuple[int, int]) -> None:
        super().__init__()
        self.station_id = random() % 256
        self.leader = leader
        self.speed = speed
        self.station_characteristics = __Station_Characteristics()
        self.reference_position = __Reference_Position(lane=lane, position=position)
        return None

    def to_dict(self) -> dict: 
        return {
            'station_id': self.station_id, 
            'leader': self.leader, 
            'speed': self.speed, 
            'station_characteristics': asdict(self.station_characteristics),
            'reference_position': asdict(self.reference_position)
        }

    @classmethod
    def from_dict(cls, j_dict):
        return cls(
            lane=j_dict['reference_position']['lane'], 
            leader=j_dict['leader'], 
            speed=j_dict['speed'], 
            position=j_dict['reference_position']['position']
        )

