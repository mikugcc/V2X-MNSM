from __future__ import annotations
from abc import ABCMeta, abstractclassmethod, abstractmethod

class Body(metaclass=ABCMeta): 

    @abstractmethod
    def to_dict(self) -> dict: 
        raise NotImplementedError(self.to_dict)

    @abstractclassmethod
    def from_dict(cls, j_dict) -> Body: 
        raise NotImplementedError(cls.from_dict)