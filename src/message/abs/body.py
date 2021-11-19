from abc import ABCMeta, abstractclassmethod, abstractmethod
from __future__ import annotations

class Body(ABCMeta): 

    @abstractmethod
    def to_dict(self) -> dict: 
        raise NotImplementedError(self.to_dict)

    @abstractclassmethod
    def from_dict(cls, j_dict) -> Body: 
        raise NotImplementedError(cls.from_dict)