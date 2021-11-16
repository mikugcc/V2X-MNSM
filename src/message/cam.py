import json
from typing import List, Tuple, Optional
from datetime import datetime as Datetime

class MsgBuilder(object): 

    def __init__(self, 
        time: float, 
        position: Tuple, 
        speed: int, 
        leader: Optional[str]
    ) -> None:
        self.time = time
        self.position = position
        self.speed = speed
        self.leader = leader
        return None 
    
    def __str__(self):
        return json.dumps({
            'time': str(self.time), 
            'position': str(self.position), 
            'speed': str(self.speed), 
            'leader': str(self.leader)
        })
    
    @property
    def serialisation(self)->str:
        return self.__str__()
