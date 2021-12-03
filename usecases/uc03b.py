import os
from typing import List
from mininet.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import mesh, wmediumd
from mininet.log import info, setLogLevel
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import *
from v2xmnsm.main.extension.mnwf.node import MnwfNode

UC03B_STATES = [
    'ALL_STOP', 
    'BEFORE_VERTICAL_PASS',
    'VERTICAL_PASS', 
    'BEFORE_HORIZONTAL_PASS',
    'HORIZONTAL_PASS'
]

class UC03bVehicle(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
    
    @property
    def name(self) -> str: 
        return f'{self.__class__.name} :: {self.__v2x_vlc.name}'
    
    @SumoStepListener.SUBSTEP(priority=9)
    def __sendCAM(self) -> None:
        vlc_cam = CAM(
            car_id = self.__v2x_vlc.name, 
            lane = self.__v2x_vlc.lane_index, 
            leader = self.__v2x_vlc.get_leader_with_distance()[0], 
            speed = self.__v2x_vlc.get_speed(), 
            position = self.__v2x_vlc.position, 
            timestamp = self.cur_time
        )
        self.__v2x_vlc.broadcast_by_mesh(vlc_cam)

class UC03bTfcLight(SumoStepListener): 
    
    def __init__(self, v2x_tfl: V2xTfcLight):
        super().__init__()
        self.__v2x_tfl = v2x_tfl

    @property
    def name(self) -> str: 
        return f'{self.__class__.name} :: {self.__v2x_tfl.tfl_id}'

    @SumoStepListener.SUBSTEP(10)
    def __handle_incoming(self):
        mps_queue = self.__v2x_tfl.mesh_packages
        for _ in range(mps_queue.qsize()): 
            cur_packet = mps_queue.get()
            cam: CAM = json_to_package(cur_packet)
            pkt_lane = cam.body.reference_position.lane
            if pkt_lane == None: continue 
            if 'HORIZONTAL_PASS' not in self.__v2x_tfl.state: 
                self.__v2x_tfl.state = 'BEFORE_HORIZONTAL_PASS'
        return None

    @SumoStepListener.SUBSTEP(9)
    def __stop_all(self): 
        if self.__v2x_tfl.state != 'ALL_STOP': return None
        denm = DENM(
            car_id=self.__v2x_tfl.tfl_id, 
            event=TRFFICLIGHT_RED, 
            lane='None', 
            position=(0,0,0), 
            timestamp=self.cur_time
        )
        self.__v2x_tfl.broadcast_by_mesh(denm)


def topology():
    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    info("*** Creating nodes\n")
    car1 = net.addCar('car1', wlans=2, encrypt=[None, None])
    car2 = net.addCar('car2', wlans=2, encrypt=[None, None])
    tflc = net.addCar('gneJ1', wlans=2, encrypt=[None, None], position='0,0,0')
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)
    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()
    for node in net.cars: 
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
    cfg_file_path = os.path.join(project_path, 'sumocfg', 'uc03b' ,'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    mnwf_nodes:List[MnwfNode] = [
        V2xVehicle('car1', car1), 
        V2xVehicle('car2', car2), 
        V2xTfcLight('gneJ1', UC03B_STATES, tflc)
    ]
    for index, node in enumerate(mnwf_nodes, 1): 
        node.mesh_intf.setRange(20)
        node.mesh_intf.setIP(ipstr=f'192.168.0.{index}', prefixLen=24)
        node.mesh_intf.updateIP()
        node.wifi_intf.setRange(200)
        node.wifi_intf.setIP(ipstr=f'192.168.1.{index}', prefixLen=24)
        node.wifi_intf.updateIP()
    sumo_ctl.add(UC03bVehicle(mnwf_nodes[0]))
    sumo_ctl.add(UC03bVehicle(mnwf_nodes[1]))
    sumo_ctl.add(UC03bTfcLight(mnwf_nodes[2]))
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


