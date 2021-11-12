from typing import Optional
import traci, traceback, sys
from threading import Thread
from abc import ABCMeta, abstractmethod



class SumoControlThread(Thread): 

    def simulation_time(): 
        return traci.simulation.getTime()
    
    def __init__(self, name, port:int=8813, order:int=1):
        Thread.__init__(self,name=name)   
        traci.init(port)
        traci.setOrder(order)

    def run(self): 
        simulation = traci.simulation
        while simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        traci.close()
    
    def add(self, listener: traci.StepListener) -> Optional[int]:
        return traci.addStepListener(listener)
    
    def remove(self, listener: traci.StepListener) -> bool:
        return traci.removeStepListener(listener)


        

class SumoStepListener(traci.StepListener, metaclass=ABCMeta):

    def __init__(self) -> None:
        super().__init__() 

    '''
    It is an abstract method. 
    The method will be invoked exact once in each traci step
    '''
    @abstractmethod
    def _step_core(self) -> bool: pass

    '''
    An implementation for the abstract method, traci.StepListener.step() 
    The parameter t is the number of steps executed. In this implementation, 
    our program will execute `t` times _step_core method. It will always 
    return True even when the _step_core throws an error, because the program 
    will stop if the step method return False.
    '''
    def step(self,t):
        if t == 0: t = 1 
        for _ in range(t): 
            try:
                self._step_core()
            except Exception: 
                traceback.print_exception(*sys.exc_info())
        return True 
    

