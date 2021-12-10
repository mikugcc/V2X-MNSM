#!/usr/bin/python3
import os
from mn_wifi.link import wmediumd, mesh as Mesh
from mn_wifi.wmediumdConnector import interference

from v2xmnsm.sumo import SumoInvoker, SumoControlThread, SumoStepListener
from v2xmnsm.mnwf import NetBuilder, MnwfCli
from v2xmnsm.msgs import DENM, OBSTACLE, json_to_package
from v2xmnsm import V2xVehicle, DataRecorder

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
            self.__v2x_vlc.broadcast_by_wifi(vlc_denm.to_json())
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

if __name__ == '__main__':
    net_builder = NetBuilder(wmediumd, interference)
    net_builder.propagation_model(model="logDistance", exp=4.5)
    net_builder.new_access_point('e1').opt_args(
        mac='00:00:00:11:00:01', channel='1', mode = 'g',
        ssid='vanet-ssid', passwd='123456789a', encrypt='wpa2', 
        position='100,25,0', failMode='standalone', datapath='user', 
        range=200
    )
    for index, cname in enumerate(['obs', 'car1', 'car2'], 1):
        car = net_builder.new_car(cname)
        car.add_intf(
            ip_v4=(f'192.168.0.{index}', 24), 
            protocol=Mesh, ssid='meshNet', 
            channel=5, ht_cap='HT40+', range=20
        )
        car.add_intf(
            ip_v4=(f'192.168.1.{index}', 24), 
            encrypt='wpa2', is_link=False, range=200
        )
    net = net_builder.build()

    net.telemetry(
        nodes=net.cars[1:3] + net.aps, 
        data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )

    project_path = os.path.dirname(os.path.abspath(__file__))
    net.useExternalProgram(SumoInvoker, 
        port=8813, clients=2, exec_order=0,
        config_file=os.path.join(project_path, 'conf','map.sumocfg'),
        extra_params=['--delay', '1000', '--start', 'false']
    )

    vlcs = [ 
        V2xVehicle('car1', net.cars[1]), 
        V2xVehicle('car2', net.cars[2]) 
    ]
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER', verbose=True)
    sumo_ctl.add(UC01CarController(vlcs[0], 1))
    sumo_ctl.add(DataRecorder(vlcs[0], f'{project_path}/output'))
    sumo_ctl.add(UC01CarController(vlcs[1], 0))
    sumo_ctl.add(DataRecorder(vlcs[1], f'{project_path}/output'))
    sumo_ctl.setDaemon(True)
    sumo_ctl.start()

    cli = MnwfCli(net)
    cli.start()
    cli.join()
