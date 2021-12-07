import os

from mininet.log import info, setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.link import mesh as Mesh
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import *

class UC02CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, speed: int = 13):
        super().__init__()
        self.__cur_lane = 1
        self.__cur_speed = speed
        self.__v2x_vlc = v2x_vlc

    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
        
    @SumoStepListener.Substeps(priority=9)
    def __sendCAM(self) -> None:
        vlc_cam = CAM(
            car_id = self.__v2x_vlc.name, 
            lane = self.__v2x_vlc.lane, 
            leader = self.__v2x_vlc.get_leader_with_distance()[0], 
            speed = self.__v2x_vlc.speed, 
            position = self.__v2x_vlc.position, 
            timestamp = self.cur_time
        )
        self.__v2x_vlc.broadcast_by_mesh(vlc_cam)

    @SumoStepListener.Substeps(priority=8)
    def __handle_in_cam(self) -> None:
        leader_car, dis_with_leader = self.__v2x_vlc.get_leader_with_distance()
        for _ in range(self.__v2x_vlc.mesh_packages.qsize()): 
            package_str = self.__v2x_vlc.mesh_packages.get_nowait()
            package: CAM = json_to_package(package_str)
            if package.header.from_car_id != leader_car: continue
            if dis_with_leader >= 75 and self.__cur_speed <= package.body.speed: continue
            self.__cur_lane ^= 1
            print(package)
        return None
    
    @SumoStepListener.Substeps(priority=1)
    def __update_state(self) -> None:
        self.__v2x_vlc.lane = self.__cur_lane
        self.__v2x_vlc.speed = self.__cur_speed
        return None

def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."

    info("*** Creating nodes\n")
    for name in ['car1', 'car2']: 
        net.addCar(name, wlans=2, encrypt=[None, 'wpa2'])
    
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()
    for car in net.cars: 
        net.addLink(
            car, cls=Mesh, intf=car.wintfs[0].name, 
            ssid='meshNet', channel=5, ht_cap='HT40+'
        )

    info("*** Starting network\n")
    net.build()
    # Track the position of the nodes
    net.telemetry(
        nodes=net.cars, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )

    info("***** Telemetry Initialised\n")
    project_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.join(project_path, 'sumocfg', 'uc02' ,'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )

    vlcs = [ 
        V2xVehicle('car1', net.cars[0]), 
        V2xVehicle('car2', net.cars[1]) 
    ]
    for i, vlc in enumerate(vlcs, 1): 
        vlc.mesh_intf.setRange(20)
        vlc.mesh_intf.setIP(ipstr=f'192.168.0.{i}', prefixLen=24)
        vlc.mesh_intf.updateIP()
        vlc.wifi_intf.setRange(200)
        vlc.wifi_intf.setIP(ipstr=f'192.168.1.{i}', prefixLen=24)
        vlc.wifi_intf.updateIP()
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(UC02CarController(vlcs[0], 5))
    sumo_ctl.add(DataRecorder(vlcs[0], f'usecases/output/uc02'))
    sumo_ctl.add(UC02CarController(vlcs[1], 20))
    sumo_ctl.add(DataRecorder(vlcs[1], f'usecases/output/uc02'))
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
