from threading import Thread
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
        


