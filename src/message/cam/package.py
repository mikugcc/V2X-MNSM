import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from .body import CamBody
from ..header import Header
from ..abs.package import Package

OBSTACLE = 0

class CamPackage(Package): 

    def __init__(self, 
        car_id: str, lane: str, leader:str, speed: int, position: Tuple[int, int], 
        timestamp:int=datetime.now().timestamp()
    ) -> None:
        self.__header: Optional[Header] = Header(car_id, 'CAM', generated_time=timestamp) if car_id is not None else None
        self.__body: Optional[CamBody] = CamBody(lane, leader, speed, position) if lane is not None else None
        return None 

    
    @property
    def header(self) -> Header: 
        return self.__header

    @property
    def body(self) -> CamBody: 
        return self.__body
    
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
        out.__header = Header.from_dict(j_dict['header'])
        out.__body = CamBody.from_dict(j_dict['body'])
        return out

    def __str__(self):
        newline,newindent = '\n', '\t'
        return f"""
----------------------START HEADER----------------------
{newline.join([f'{key}:{newindent*2}{value}' for key, value in self.header.to_dict().items()])}
-----------------------END HEADER-----------------------

-----------------------START BODY-----------------------
{newline.join([f'{key}:{newindent*2}{value}' for key, value in self.body.to_dict().items()])}
------------------------END BODY------------------------
"""