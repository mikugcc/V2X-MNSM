import os

from datetime import datetime
from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mn_wifi.link import mesh, wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Car as MNCar
from mn_wifi.node import Node_wifi as WiFiNode
from mn_wifi.wmediumdConnector import interference

from src import *

class TrafficLightController(SumoStepListener): 

    def __init__(self, mnwf_node: MnwfVehicle):
        super().__init__()
        self.__step_num = 0
        self.__is_stoped = False
        self.__mnwf_node = mnwf_node

    @SumoStepListener.SUBSTEP(10)
    def __handle_traffic_light(self):
        self.__step_num += 1
        if self.__step_num % 65 != 0: return
        if(self.__is_stoped): # START 
            self.__is_stoped = False
            red_light_on = DENM(
                car_id='trafficlight', 
                event=TRFFICLIGHT_GREEN, 
                lane=-1, position=(-1,-1),
                timestamp=self.cur_time
            )
            self.__mnwf_node.broadcast(red_light_on)
        else: # STOP
            self.__is_stoped = True
            red_light_on = DENM(
                car_id='trafficlight', 
                event=TRFFICLIGHT_RED, 
                lane=-1, position=(-1,-1),
                timestamp=self.cur_time
            )
            self.__mnwf_node.broadcast(red_light_on)

def topology():
    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")

    car = net.addCar('car', wlans=2, encrypt=[None, None])
    tfcl = net.addCar('trfic', wlans=2, encrypt=[None, None], position='0,0,0')
    
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    for node in [car, tfcl]: 
        net.addLink(
            node, cls=mesh, intf=node.wintfs[0].name, 
            ssid='meshNet', channel=5, ht_cap='HT40+', range=5
        )        


    info("*** Starting network\n")
    net.build()

    for enb in net.aps: enb.start([])

    # Track the position of the nodes
    nodes = net.cars + net.aps

    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-150, min_y=-100,
        max_x=150, max_y=100
    )
    
    info("***** Telemetry Initialised\n")
    project_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.join(project_path, 'sumocfg', 'uc03a' ,'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    v2x_vlc = V2xVehicle('car', car)
    v2x_vlc.mesh_intf.setRange(100)
    v2x_vlc.mesh_intf.setIP(ipstr=f'192.168.0.1', prefixLen=24)
    v2x_vlc.mesh_intf.updateIP()
    v2x_vlc.wifi_intf.setRange(200)
    v2x_vlc.wifi_intf.setIP(ipstr=f'192.168.1.2', prefixLen=24)
    v2x_vlc.wifi_intf.updateIP()
    sumo_ctl.add(CarController(v2x_vlc))
    sumo_ctl.add(TrafficLightController(MnwfVehicle(tfcl)))
    sumo_ctl.add(DataRecorder([v2x_vlc], f'output/uc03/{datetime.now().strftime("%b%d-%H%M%S")}'))
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


