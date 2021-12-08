import os
from typing import List

from mininet.log import info, setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.link import mesh as Mesh
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

from v2xmnsm.sumo import SumoStepListener, SumoInvoker, SumoControlThread
from v2xmnsm.msgs import DENM, OBSTACLE, json_to_package
from v2xmnsm import V2xVehicle

class UC04Car1Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = start_lane
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
    
    @SumoStepListener.Substeps(priority=9)
    def __detact_obstruction(self) -> None:
        if self.__v2x_vlc.speed == 0: return None
        if self.__v2x_vlc.distance < 70: return None
        vlc_denm = DENM(
            car_id = self.__v2x_vlc.name, 
            event = OBSTACLE, 
            lane = self.__cur_lane, 
            position = self.__v2x_vlc.position, 
            timestamp = self.cur_time
        )
        self.__v2x_vlc.broadcast_by_mesh(vlc_denm.to_json())
        return None
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__v2x_vlc.mesh_packages.qsize()): 
            package_str = self.__v2x_vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.body.situation.cause != OBSTACLE: continue
            from_car_id = package.header.from_car_id
            if from_car_id != self.__v2x_vlc.name: continue 
            self.__v2x_vlc.speed = 0
            print(f'{self.__v2x_vlc.name} stops')
        self.__v2x_vlc.lane = self.__cur_lane
        return None
    
class UC04Car2Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = start_lane
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__v2x_vlc.mesh_packages.qsize()): 
            package_str = self.__v2x_vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.body.situation.cause != OBSTACLE: continue
            self.__cur_lane = package.body.location.lane ^ 1
            print(f'{self.__v2x_vlc.name} changes lane to {self.__cur_lane}')
        self.__v2x_vlc.lane = self.__cur_lane
        return None

class UC04Car3Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = start_lane
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__v2x_vlc.mesh_packages.qsize()): 
            package_str = self.__v2x_vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.body.situation.cause != OBSTACLE: continue
            self.__v2x_vlc.speed *= 2
            print(f'{self.__v2x_vlc.name} speeds up')
        self.__v2x_vlc.lane = self.__cur_lane
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
    for car in net.cars[1:]: 
        net.addLink(
            car, cls=Mesh, intf=car.wintfs[0].name, 
            ssid='meshNet', channel=5, ht_cap='HT40+'
        )

    info("*** Starting network\n")
    net.build()
    for enb in net.aps: enb.start([])

    # Track the position of the nodes
    nodes = net.cars[1:] + net.aps
    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )

    info("***** Telemetry Initialised\n")
    usecases_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.join(usecases_path, 'sumocfg', 'uc04' ,'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    vlcs = [ 
        V2xVehicle('car1', net.cars[1]), 
        V2xVehicle('car2', net.cars[2]), 
        V2xVehicle('car3', net.cars[3])
    ]
    for i, vlc in enumerate(vlcs, 1): 
        vlc.mesh_intf.setRange(25)
        vlc.mesh_intf.setIP(ipstr=f'192.168.0.{i}', prefixLen=24)
        vlc.mesh_intf.updateIP()
        vlc.wifi_intf.setRange(200)
        vlc.wifi_intf.setIP(ipstr=f'192.168.1.{i}', prefixLen=24)
        vlc.wifi_intf.updateIP()
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(UC04Car1Controller(vlcs[0], 1))
    sumo_ctl.add(UC04Car2Controller(vlcs[1], 1))
    sumo_ctl.add(UC04Car3Controller(vlcs[2], 0))
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
