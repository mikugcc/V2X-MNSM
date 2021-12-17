import json
from datetime import datetime
from random import random
from typing import Dict, Optional, Tuple
from .body import CamBody
from ..header import Header
from ..abs.package import Package

OBSTACLE = 0

class CamPackage(Package): 

    def __init__(self, 
        from_id: str, lane: str, leader:str, speed: int, position: Tuple[int, int], 
        timestamp:float=datetime.now().timestamp()
    ) -> None:
        self.__header = Header(from_id, 'CAM', 0, Package._new_id(), timestamp) if from_id is not None else None
        self.__body = CamBody(lane, leader, speed, position) if lane is not None else None
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
        cam_header = self.header.to_dict()
        cam_body = self.body.to_dict()
        return f"""
----------------------START HEADER----------------------
{newline.join([f'{key}:{newindent*2}{value}' for key, value in cam_header.items()])}
-----------------------END HEADER-----------------------

-----------------------START BODY-----------------------
********************* META DATA ***********************
station_id: {newindent*2} {cam_body['station_id']}
leader: {newindent*2} {cam_body['leader']}
speed: {newindent*2} {cam_body['speed']}
*************** STATION CHARACTERISTICS ***************
{newline.join([f'{key}:{newindent*2}{value}' for key, value in cam_body['station_characteristics'].items()])}
***************** REFERENCE POSITION ******************
{newline.join([f'{key}:{newindent*2}{value}' for key, value in cam_body['reference_position'].items()])}
------------------------END BODY------------------------
"""