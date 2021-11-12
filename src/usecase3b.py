from typing import List
from mininet.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.log import info, setLogLevel
from mn_wifi.node import Node_wifi as WiFiNode, Car as MNCar
from mn_wifi.link import mesh, wmediumd
from mn_wifi.wmediumdConnector import interference
from extension import V2xSumo
from utils import Type, DENM, async_func
from utils import SumoControlThread, VlcStepController, VlcControlUtil as SMCar
import os

class TrafficLightController(VlcStepController): 

    def __init__(self, mnwf_node: WiFiNode):
        super().__init__(None, None)
        self.__step_num = 0
        self.__is_stoped = False
        self.__mnwf_node = mnwf_node

    def _step_core(self):
        self.__step_num += 1
        if self.__step_num % 65 != 0: return
        if(self.__is_stoped): # START 
            self.__is_stoped = False
            start_cmd = DENM(type=Type.START)
            self.__mnwf_node.popen([
                'udp_bcs_sdr', 
                '192.255.255.255', 
                '9090', 
                start_cmd.serialisation
            ])
        else: # STOP
            self.__is_stoped = True
            stop_cmd = DENM(type=Type.STOP)
            self.__mnwf_node.popen([
                'udp_bcs_sdr', 
                '192.255.255.255', 
                '9090', 
                stop_cmd.serialisation
            ])

class CarController(VlcStepController): 

    def __init__(self, sm_car: SMCar, mnwf_car: MNCar):
        super().__init__(sm_car, mnwf_car)
        self.__cur_lane = 0
        self.__msg_queue:List[DENM] = [] 
        self.__is_listen = False
    
    @async_func
    def listen_message(self):
        self.__is_listen = True
        rcv_str, _, _ = self._mnwf_car.pexec(['udp_rcv', '192.255.255.255', '9090'])
        rcv_cmd = DENM(str_cmd=rcv_str)
        print(f'{self._sumo_car.name} receives data {rcv_cmd}')
        self.__msg_queue.append(rcv_cmd)
        self.__is_listen = False
        

    def _step_core(self):
        # If not start new thread there, 
        # There will be an exception from socket 
        if not self.__is_listen: self.listen_message()
        while self.__msg_queue:
            vlc_cmd = self.__msg_queue.pop()
            if vlc_cmd.type == Type.STOP: 
                self._sumo_car.stop()
            elif vlc_cmd.type == Type.START: 
                self._sumo_car.restart()
        self._sumo_car.lane_index = self.__cur_lane
        return None
    


def topology():
    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")

    car1 = net.addCar('car1', wlans=1, encrypt=[''])
    car2 = net.addCar('car2', wlans=1, encrypt=[''])
    tfcl = net.addCar('trfic', wlans=1, encrypt=[''], position='0,0,0')
    
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    for node in [car1, car2, tfcl]: 
        net.addLink(
            node, cls=mesh, intf=node.intfNames()[0], 
            ssid='meshNet', channel=5, ht_cap='HT40+', range=5
        )        


    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])
    
    for i, mn_car in enumerate([car1, car2, tfcl], start=1): 
        mn_car.setIP(ip=f'192.168.0.{i}', intf=mn_car.wintfs[0].name)

    # Track the position of the nodes
    nodes = net.cars + net.aps

    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-150, min_y=-100,
        max_x=150, max_y=100
    )
    
    info("***** Telemetry Initialised\n")
    project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_file_path = os.path.join(project_root_path, 'sumocfg', 'uc03b', 'map.sumocfg')
    net.useExternalProgram(
        program=V2xSumo, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(CarController(SMCar('car1'), car1))
    sumo_ctl.add(CarController(SMCar('car2'), car2))
    sumo_ctl.add(TrafficLightController(tfcl))
    sumo_ctl.start()
    info("***** TraCI Initialised\n")

    CLI(net)

    info("***** CLI Initialised\n")

    info("*** Stopping network\n")
    net.stop()
    return None


if __name__ == '__main__':
    setLogLevel('info')
    topology()


