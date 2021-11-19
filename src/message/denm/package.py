import json
from typing import Dict, Optional, Tuple
from src.message.header import Header
from src.message.denm.body import DenmBody
from src.message.abs.package import Package

OBSTACLE = 0

class DenmPackage(Package): 

    def __init__(self, car_id: str, event: int, lane: str, position: Tuple[int, int]) -> None:
        self.header: Optional[Header] = Header(car_id, 'DENM') if car_id is not None else None
        self.body: Optional[DenmBody] = DenmBody(event, lane, position) if event is not None else None
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
        out = cls(None, None, None, None)
        out.header = Header.from_dict(j_dict['header'])
        out.body = DenmBody.from_dict(j_dict['body'])
        return out

    def __str__(self):
        header_dict = self.header.to_dict()
        body_dict = self.body.to_dict()
        return \
f'''
----------------------START HEADER----------------------
{'\n'.join(f'{key}:\t{value}' for key, value in header_dict.items())}
-----------------------END HEADER-----------------------

-----------------------START BODY-----------------------
********************* MANAGEMENET *********************
{'\n'.join(f'{key}:\t{value}' for key, value in body_dict['management'].items())}
********************** SITUATION **********************
{'\n'.join(f'{key}:\t{value}' for key, value in body_dict['situation'].items())}
*********************** LOCATION **********************
{'\n'.join(f'{key}:\t{value}' for key, value in body_dict['location'].items())}
------------------------END BODY------------------------
'''