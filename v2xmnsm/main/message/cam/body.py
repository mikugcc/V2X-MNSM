from typing import Tuple
from random import random
from dataclasses import asdict, dataclass, field
from ..abs.body import Body

@dataclass(frozen=True)
class StationCharacteristics: 
    mobile_its_station: bool = field(default=False) # ITS station which we did not implement
    private_its_station: bool = field(default=False) # we also did not implement
    physical_relevant_its_station: bool = field(default=False) # we also did not implement

@dataclass(frozen=True)
class ReferencePosition: 
    lane: str # NOT IN ORIGIN DENM BUT WE ADDED IT HERE
    position: Tuple[int, int]
    elevation: int = field(default=0)
    heading: int = field(default=0)

class CamBody(Body): 
    def __init__(self, lane: str, leader: str, speed: int, position: Tuple[int, int]) -> None:
        super().__init__()
        self.station_characteristics = StationCharacteristics(False, False, False)
        self.reference_position = ReferencePosition(lane=lane, position=position)
        self.station_id = random() % 256
        self.leader = leader
        self.speed = speed

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

