from logging import warning
from threading import Thread
from mn_wifi.net import Car as MNCar
from .sumo_vlc import VlcControlUtil as SMCar
from abc import ABCMeta, abstractmethod
import traci

class SumoControlThread(Thread): 
    
    def __init__(self, name, port:int=8813, order:int=1):
        Thread.__init__(self,name=name)   
        self._sumo_traci = traci
        traci.init(port)
        traci.setOrder(order)

    def run(self): 
        simulation = traci.simulation
        while simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        traci.close()
    

    def add(self, listener: traci.StepListener):
        traci.addStepListener(listener)
        

class VlcStepController(traci.StepListener, metaclass=ABCMeta):

    def __init__(self, sumo_car: SMCar, mnwf_car: MNCar) -> None:
        super().__init__() 
        self._sumo_car = sumo_car
        self._mnwf_car = mnwf_car

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
            except Exception as e: 
                print(f'THERE IS A ERROR DURING EXECUTING\n\t{str(e)}')
                raise e
        return True 
    

