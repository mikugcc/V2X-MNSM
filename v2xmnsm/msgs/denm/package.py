import json
from random import random
from datetime import datetime
from typing import Dict, Optional, Tuple
from ..header import Header
from .body import DenmBody
from ..abs.package import Package

OBSTACLE = 0
TRFFICLIGHT_RED = 1
TRFFICLIGHT_GREEN = 2
LANE_CHANGING = 3

class DenmPackage(Package): 

    def __init__(
        self, from_id: str, event: int, lane: str, position: Tuple[int, int],
        timestamp:float=datetime.now().timestamp()
    ) -> None:
        self.__header = Header(from_id, 'DENM', 0, Package._new_id(), timestamp) if from_id is not None else None
        self.__body = DenmBody(event, lane, position) if event is not None else None
        return None 

    @property
    def header(self) -> Header: 
        return self.__header

    @property
    def body(self) -> DenmBody: 
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
        out = cls(None, None, None, None)
        out.__header = Header.from_dict(j_dict['header'])
        out.__body = DenmBody.from_dict(j_dict['body'])
        return out

    def __eq__(self, other): 
            if not isinstance(other, self.__class__): return NotImplemented
            return self.to_json == other.to_json

    def __str__(self):
        newline,newindent = '\n', '\t'
        header_dict = self.header.to_dict()
        body_dict = self.body.to_dict()
        return f"""
----------------------START HEADER----------------------
{newline.join([f'{key}:{newindent*2}{value}' for key, value in header_dict.items()])}
-----------------------END HEADER-----------------------

-----------------------START BODY-----------------------
********************* MANAGEMENET *********************
{newline.join([f'{key}:{newindent*2}{value}' for key, value in body_dict['management'].items()])}
********************** SITUATION **********************
{newline.join([f'{key}:{newindent*2}{value}' for key, value in body_dict['situation'].items()])}
*********************** LOCATION **********************
{newline.join([f'{key}:{newindent*2}{value}' for key, value in body_dict['location'].items()])}
------------------------END BODY------------------------
"""