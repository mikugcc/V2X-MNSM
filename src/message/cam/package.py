import json
from typing import Dict, Optional, Tuple
from cam.body import Body
from src.message.header import Header
from src.message.abs.package import Package

OBSTACLE = 0

class CamPackage(Package): 

    def __init__(self, car_id: str, lane: str, leader:str, speed: int, position: Tuple[int, int]) -> None:
        self.header: Optional[Header] = Header(car_id, 'CAM') if car_id is not None else None
        self.body: Optional[Body] = Body(lane, leader, speed, position) if lane is not None else None
        return None 
    
    def to_json(self) -> str: 
        return json.dumps({
            'header': self.header.to_dict(), 
            'body': self.body.to_dict()
        })

    @classmethod
    def from_json(cls, json_str: str):
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_dict(cls, j_dict: Dict):
        out = cls(None, None, None, None, None)
        out.header = Header.from_dict(j_dict['header'])
        out.body = Body.from_dict(j_dict['body'])
        return out

    def __str__(self):
        return \
f'''
----------------------START HEADER----------------------
{'\n'.join(f'{key}:\t{value}' for key, value in self.header.to_dict().items())}
-----------------------END HEADER-----------------------

-----------------------START BODY-----------------------
{'\n'.join(f'{key}:\t{value}' for key, value in self.body.to_dict().items())}
------------------------END BODY------------------------
'''