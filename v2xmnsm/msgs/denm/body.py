from random import random
from typing import Tuple
from dataclasses import asdict, dataclass, field

@dataclass(frozen=True)
class Management: 
    station_id: int = field(default=0) # ITS station which we did not implement
    sequence_id: int = field(default=0) # we also did not implement sequenct id
    data_version: int = field(default=0) # [0,255]
    expirity_time: int = field(default=0) # [0, 2^{48}-1]
    frequency: int = field(default=0) #[0, 255]
    reliablity: int = field(default=100) #[0, 100]
    is_negation: bool = field(default=False)

@dataclass(frozen=True)
class DecentralizedSituation: 
    cause: int # [0, 2^{6}-1]
    subcause: int # [0, 2^{6}-1]
    severity: int = field(default=2) # (1,2,3,4)

@dataclass(frozen=True)
class Location: 
    lane: int # NOT IN ORIGIN DENM BUT WE ADDED IT HERE
    position: Tuple[int, int]
    elevation: int = field(default=0)
    trace_id: int = field(default=0)
    way_point: Tuple[int, int, int] = field(default=(0,0,0))

class DenmBody(object): 
    def __init__(self, event: int, lane: str, position: Tuple[int, int]) -> None:
        super().__init__()
        self.management = Management()
        self.situation = DecentralizedSituation(cause=event, subcause=0)
        self.location = Location(lane, position)

    def to_dict(self) -> dict: 
        return {
            'management': asdict(self.management),
            'situation': asdict(self.situation),
            'location': asdict(self.location)
        }

    @classmethod
    def from_dict(cls, j_dict):
        dsq_body = cls(
            event=j_dict['situation']['cause'], 
            lane=j_dict['location']['lane'], 
            position=j_dict['location']['position']
        )
        return dsq_body

