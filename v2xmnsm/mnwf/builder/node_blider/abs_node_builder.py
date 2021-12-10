
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from mn_wifi.net import Mininet_wifi

class AbsNodeBuilder(metaclass=ABCMeta): 

    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def build_node(self) -> None: 
        raise NotImplementedError(self.build_node)

    @abstractmethod
    def build_links(self) -> None: 
        raise NotImplementedError(self.build_links)

    @abstractmethod
    def configure(self) -> None: 
        raise NotImplementedError(self.configure)