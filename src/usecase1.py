from typing import List, Dict, Any
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import mesh as Mesh, wmediumd
from mn_wifi.wmediumdConnector import interference
from message import *
from extension import *
import os

class CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = 0

    def __detact_obstruction(self) -> int: 
        leader, gap_with = self.__v2x_vlc.get_leader_with_distance()
        if (leader != 'obs' or gap_with >= 50): return -1 
        return self.__v2x_vlc.lane_index

    def before_listening(self):
        return super().before_listening()

    @SumoStepListener.SUBSTEP(priority=10)
    def __send_cam(self) -> None: 
        vlc_cam = CAM(
            car_id = self.__v2x_vlc.name, 
            lane = self.__v2x_vlc.lane_index, 
            leader = self.__v2x_vlc.get_leader_with_distance()[0], 
            speed = self.__v2x_vlc.get_speed(), 
            position = self.__v2x_vlc.position
        )
        self.__v2x_vlc.broadcast_by_wifi(vlc_cam.to_json())
        return None
    
    @SumoStepListener.SUBSTEP(priority=10)
    def __send_denm(self) -> None: 
        obs_lane_index = self.__detact_obstruction()
        if obs_lane_index >= 0:
            self.__cur_lane = obs_lane_index ^ 1 
            vlc_denm = DENM(
                self.__v2x_vlc.name, 
                OBSTACLE, 
                obs_lane_index, 
                self.__v2x_vlc.position
            )
            self.__v2x_vlc.broadcast_by_wifi(vlc_denm.to_json())
        self.__v2x_vlc.lane_index = self.__cur_lane
        return None

    @SumoStepListener.SUBSTEP(priority=5)
    def __handle_in_msg(self) -> None:
        while not self.__v2x_vlc.wifi_packages_queue.empty(): 
            data_package_str = self.__v2x_vlc.wifi_packages_queue.get()
            package = json_to_package(data_package_str)
            if package.header.from_car_id == self.__v2x_vlc.name: continue
            if package.header.proto_type != 'DENM': continue
            vlc_denm: DENM = package
            if vlc_denm.body.situation.cause == OBSTACLE: 
                self.__cur_lane = vlc_denm.body.location.lane ^ 1
        self.__v2x_vlc.lane_index = self.__cur_lane
        return None

    @SumoStepListener.SUBSTEP(priority=1)
    def __record_data(self) -> None: 
        
        return None


def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."
    info("*** Creating nodes\n")

    for name in ['obs', 'car1', 'car2', 'car3']: 
        net.addCar(name, wlans=2, encrypt=[None, 'wpa2'])

    kwargs = {
        'ssid': 'vanet-ssid', 
        'mode': 'g', 
        'passwd': '123456789a',
        'encrypt': 'wpa2', 
        'failMode': 'standalone', 
        'datapath': 'user'
    }
    net.addAccessPoint(
        'e1', mac='00:00:00:11:00:01', channel='1',
        position='100,25,0', range=200, **kwargs
    )
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    for node in net.cars[1:3]: 
        net.addLink(
            node, cls=Mesh, intf=node.intfNames()[0], 
            ssid='meshNet', channel=5, ht_cap='HT40+'
        )

    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])

    # Track the position of the nodes
    nodes = net.cars[1:3] + net.aps

    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )
    info("***** Telemetry Initialised\n")
    project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_file_path = os.path.join(project_root_path, 'sumocfg', 'uc01' ,'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    vlcs = [
        V2xVehicle('car1', net.cars[1]), 
        V2xVehicle('car2', net.cars[2])
    ]

    for i, vlc in enumerate(vlcs, 1): 
        vlc.mesh_intf.setRange(1)
        vlc.mesh_intf.setIP(f'192.168.0.{i}', 24)
        vlc.mesh_intf.updateIP()
        vlc.wifi_intf.setRange(200)
        vlc.wifi_intf.setIP(f'192.168.1.{i}', 24)
        vlc.wifi_intf.updateIP()

        
    
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(CarController(vlcs[0]))
    sumo_ctl.add(CarController(vlcs[1]))
    sumo_ctl.setDaemon(True)
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


