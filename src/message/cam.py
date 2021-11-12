import json
from typing import List
from enum import Enum

class MsgBuilder(object): 

    def __init__(self, behavior: Behavior = Behavior.NULL, pars = [], str_cmd = None) -> None:
        self.__behavior = behavior
        self.__pars = pars
        if str_cmd is not None:
            init_obj = json.loads(str_cmd) 
            self.__behavior = Behavior(init_obj['command'])
            self.__pars = init_obj['parameters']
        return None 

    @property
    def behavior(self) -> Behavior:
        return self.__behavior
    
    @property
    def parameters(self) -> List: 
        return self.__pars

    def __str__(self):
        return json.dumps({
            'command': self.__behavior.name, 
            'parameters': self.__pars
        })
    
    @property
    def serialisation(self)->str:
        return json.dumps({
            'command': self.__behavior.value, 
            'parameters': self.__pars
        }).replace(' ', '')