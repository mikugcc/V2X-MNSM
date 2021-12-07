import os
from typing import List

from mininet.log import info, setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.link import mesh as Mesh
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import *

class UC01CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = start_lane
        self.__package_cache = set()
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
    
    @SumoStepListener.Substeps(priority=9)
    def __detact_obstruction(self) -> None:
        cur_dis = self.__v2x_vlc.distance
        if 75 <= cur_dis <= 125: 
            vlc_denm = DENM(
                car_id = self.__v2x_vlc.name, 
                event = OBSTACLE, 
                lane = 0, 
                position = self.__v2x_vlc.position, 
                timestamp = self.cur_time
            )
            self.__v2x_vlc.broadcast_by_wifi(vlc_denm)
        return None
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__v2x_vlc.wifi_packages.qsize()): 
            package_str = self.__v2x_vlc.wifi_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.header.from_car_id == self.__v2x_vlc.name: continue
            if package.body.situation.cause != OBSTACLE: continue
            pkg_unique_id = str(package.body.situation.cause)+ str(package.body.location.position)
            if pkg_unique_id in self.__package_cache: continue
            self.__package_cache.add(pkg_unique_id)
            print(package)
            self.__cur_lane = package.body.location.lane ^ 1
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
    for car in net.cars[1:3]: 
        net.addLink(
            car, cls=Mesh, intf=car.wintfs[0].name, 
            ssid='meshNet', channel=5, ht_cap='HT40+'
        )

    info("*** Starting network\n")
    net.build()
    for enb in net.aps: enb.start([])

    # Track the position of the nodes
    nodes = net.cars[1:3] + net.aps
    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )

    info("***** Telemetry Initialised\n")
    usecases_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.join(usecases_path, 'sumocfg', 'uc01' ,'map.sumocfg')
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
        vlc.mesh_intf.setRange(25)
        vlc.mesh_intf.setIP(ipstr=f'192.168.0.{i}', prefixLen=24)
        vlc.mesh_intf.updateIP()
        vlc.wifi_intf.setRange(200)
        vlc.wifi_intf.setIP(ipstr=f'192.168.1.{i}', prefixLen=24)
        vlc.wifi_intf.updateIP()
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(UC01CarController(vlcs[0], 1))
    sumo_ctl.add(DataRecorder(vlcs[0], f'usecases/output/uc01'))
    sumo_ctl.add(UC01CarController(vlcs[1], 0))
    sumo_ctl.add(DataRecorder(vlcs[1], f'usecases/output/uc01'))
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
