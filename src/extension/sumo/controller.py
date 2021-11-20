from __future__ import annotations

from abc import ABCMeta
from logging import info
from functools import wraps
from threading import Thread
from typing import Callable, List, Optional, final

import traci
from traci.exceptions import TraCIException


class SumoStepListener(traci.StepListener, metaclass=ABCMeta):
    
    @classmethod
    def SUBSTEP(cls, priority: int=0):
        def __inner(task): 
            def __wrapper(*args,**kwargs): 
                return task(*args,**kwargs)
            setattr(__wrapper, 'priority', priority)
            return __wrapper
        return __inner

    def __init__(self) -> None:
        super().__init__() 
        self.__cur_step = 0
        self.__tasks: List[Callable] = []
        for _, field in self.__class__.__dict__.items():
            f_priority = getattr(field, 'priority', -1)
            if f_priority >= 0: self.__tasks.append(field)
        self.__tasks.sort(key=lambda t: -t.priority)

    @property
    def cur_time(self) -> float: 
        return traci.simulation.getTime()

    @property
    def cur_step(self) -> int: 
        return self.__cur_step

    def before_listening(self): pass

    def step(self,t) -> bool:
        '''
        An implementation for the abstract method, traci.StepListener.step() 
        The parameter t is the number of steps executed. In this implementation, 
        our program will execute `t` times _step_core method. It will always 
        return True even when the _step_core throws an error, because the program 
        will stop if the step method return False.
        '''
        if t == 0: t = 1 
        for _ in range(t): 
            self.__cur_step += 1
            self.__step_one()
        return True 

    def __step_one(self) -> bool:
        '''
        The method will be invoked exact once in each traci step
        '''
        for task in self.__tasks: 
            task(self)
        return True
    
    def after_listening(self): pass


class SumoControlThread(Thread): 
    
    def __init__(self, name, port:int=8813, priority:int=1):
        Thread.__init__(self,name=name)   
        traci.init(port)
        traci.setOrder(priority)
        self.__listeners: List[SumoStepListener] = []

    def run(self): 
        for listener in self.__listeners: listener.before_listening()
        while traci.simulation.getMinExpectedNumber() > 0:
            try: traci.simulationStep()
            except TraCIException as e: info(e.with_traceback())
        for listener in self.__listeners: listener.after_listening()
        traci.close()
    
    def add(self, listener: SumoStepListener) -> Optional[int]:
        self.__listeners.append(listener)
        return traci.addStepListener(listener)
    
    def remove(self, listener: SumoStepListener) -> bool:
        self.__listeners.remove(listener)
        return traci.removeStepListener(listener)
