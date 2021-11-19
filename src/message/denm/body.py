from typing import Tuple
from random import random
from dataclasses import asdict, dataclass
import json

@dataclass(frozen=True)
class __Management: 
    station_id: int = 0 # ITS station which we did not implement
    sequence_id: int = 0 # we also did not implement sequenct id
    data_version: int = 0 # [0,255]
    expirity_time: int = 0 # [0, 2^{48}-1]
    frequency: int = 0 #[0, 255]
    reliablity: int = 100 #[0, 100]
    is_negation: bool = False

@dataclass(frozen=True)
class __DecentralizedSituation: 
    cause: int # [0, 2^{6}-1]
    subcause: int # [0, 2^{6}-1]
    severity: int = 2 # (1,2,3,4)

@dataclass(frozen=True)
class __Location: 
    lane: int # NOT IN ORIGIN DENM BUT WE ADDED IT HERE
    position: Tuple[int, int]
    elevation: int = 0
    trace_id: int = 0
    way_point: Tuple[int, int, int] = (0,0,0)

class DenmBody(object): 
    def __init__(self, event: int, lane: str, position: Tuple[int, int]) -> None:
        super().__init__()
        self.management = __Management(sequence_id=random()%256)
        self.situation = __DecentralizedSituation(cause=event, subcause=0)
        self.location = __Location(lane, position)

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
        dsq_body.management.sequence_id=j_dict['management']['sequence_id']
        return dsq_body

