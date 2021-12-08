from __future__ import annotations
from typing import Dict
from abc import ABCMeta, abstractclassmethod, abstractmethod, abstractproperty
from .body import Body
from ..header import Header

class Package(metaclass=ABCMeta): 

    __ID_INCREASOR = 0

    @classmethod
    def _new_id(cls) -> int:
        cls.__ID_INCREASOR += 1
        return cls.__ID_INCREASOR

    @abstractproperty
    def header(self) -> Header: pass

    @abstractproperty
    def body(self) -> Body: pass

    @abstractmethod
    def to_json(self) -> str: 
        raise NotImplementedError(self.to_json)
 

    @abstractclassmethod
    def from_json(cls, j_str: str) -> Package: 
        raise NotImplementedError(cls.from_json)

    @abstractclassmethod
    def from_dict(cls, j_dict: Dict) -> Package: 
        raise NotImplementedError(cls.from_dict)

