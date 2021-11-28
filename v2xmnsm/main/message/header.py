from random import random
from datetime import datetime
from dataclasses import dataclass, asdict, field

@dataclass
class Header: 
    from_car_id: str
    proto_type: str
    proto_version:int = field(default=0)
    message_id:int = field(default=int(random() * 255))
    generated_time:float = field(default=datetime.now().timestamp()) 
        
    def to_dict(self) -> dict: 
        return asdict(self)

    @classmethod
    def from_dict(cls, j_dict):
        return cls(
            from_car_id=j_dict['from_car_id'],  
            proto_type=j_dict['proto_type'],  
            proto_version=j_dict['proto_version'], 
            message_id=j_dict['message_id'], 
            generated_time=j_dict['generated_time']
        )
