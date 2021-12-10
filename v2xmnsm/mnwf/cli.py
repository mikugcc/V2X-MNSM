import os
from io import TextIOWrapper
from enum import Enum
from typing import TextIO
from mn_wifi.cli import MN_CLI
from threading import Thread

from mn_wifi.net import Mininet_wifi

class STDType(Enum): 
    PIPE=0
    STDIN=1
    STDOUT=2    

class BiDirectPipe(object):

    def __init__(self) -> None:
        rfd, wfd = os.pipe()
        self.__reader: TextIOWrapper = os.fdopen(rfd)
        self.__writer: TextIOWrapper = os.fdopen(wfd, 'w')
    
    @property
    def reader(self) -> TextIOWrapper:
        return self.__reader
    
    @property
    def writer(self) -> TextIOWrapper: 
        return self.__writer

class MnwfCli(Thread): 

    def __init__(self, net: Mininet_wifi, **kwargs):
        super().__init__(name='Mininet-WIFI', **kwargs)
        self.__net: Mininet_wifi = net
        MN_CLI.prompt = f'$ '

    def run(self) -> None:
        MN_CLI(self.__net)
        self.__net.stop()
         