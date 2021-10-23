import json
from typing import List
from enum import Enum

class VlcCmdType(Enum): 
    NULL = -1
    STOP = 0
    START = 1
    CHANGE_TO = 2

class VlcCommand(object): 

    def __init__(self, type: VlcCmdType = VlcCmdType.NULL, pars = [], str_cmd = None) -> None:
        self.__type = type
        self.__pars = pars
        if str_cmd is not None:
            init_obj = json.loads(str_cmd) 
            self.__type = VlcCmdType(init_obj['command'])
            self.__pars = init_obj['parameters']
        return None 

    @property
    def type(self) -> VlcCmdType:
        return self.__type
    
    @property
    def parameters(self) -> List: 
        return self.__pars

    def __str__(self):
        return json.dumps({
            'command': self.__type.name, 
            'parameters': self.__pars
        })
    
    @property
    def serialisation(self):
        return json.dumps({
            'command': self.__type.value, 
            'parameters': self.__pars
        })