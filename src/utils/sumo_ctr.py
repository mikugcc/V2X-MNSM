from threading import Thread
from mn_wifi.net import Mininet_wifi
import traci

class SumoControlThread(Thread): 
    
    def __init__(self, name, net: Mininet_wifi, port:int=8813, order:int=1):
        Thread.__init__(self,name=name)   
        self._wifi_core = net
        traci.init(port)
        traci.setOrder(order)

    def run(self): 
        simulation = traci.simulation
        while simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        traci.close()
    

    def add(self, listener: traci.StepListener):
        traci.addStepListener(listener)
        


