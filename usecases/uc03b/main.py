import os
from typing import List
from mn_wifi.link import mesh as Mesh, wmediumd
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import V2xVehicle, V2xTfcLight, DataRecorder
from v2xmnsm.mnwf import MnwfNode, MnwfCli, NetBuilder
from v2xmnsm.sumo import SumoInvoker, SumoControlThread

from tfl import * 
from vlc import *

if __name__ == '__main__':
    net_builder = NetBuilder(wmediumd, interference)
    net_builder.propagation_model(model="logDistance", exp=4.5)
    net_builder.new_traffic_light('gneJ1').add_intf(
        ip_v4=(f'192.168.0.2', 24), 
        protocol=Mesh, ssid='meshNet', 
        channel=5, ht_cap='HT40+', range=50
    ).add_intf(
        ip_v4=(f'192.168.1.2', 24), 
        encrypt='wpa2', is_link=False, range=50
    )
    for index, cname in enumerate(['car1', 'car2'], 1):
        car = net_builder.new_car(cname)
        car.add_intf(
            ip_v4=(f'192.168.0.{index}', 24), 
            protocol=Mesh, ssid='meshNet', 
            channel=5, ht_cap='HT40+', range=50, txpower=20
        )
        car.add_intf(
            ip_v4=(f'192.168.1.{index}', 24), 
            encrypt='wpa2', is_link=False, range=1
        )
    net = net_builder.build()

    car1, car2, tflc = net.cars
    net.telemetry(
        nodes=[car1, car2, tflc], data_type='position',
        min_x=-150, min_y=-100, 
        max_x=150, max_y=100
    )

    project_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.join(project_path, 'conf', 'map.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )

    mnwf_nodes:List[MnwfNode] = [
        V2xVehicle('car1', car1), 
        V2xVehicle('car2', car2), 
        V2xTfcLight('gneJ1', UC03B_TFL_PHASES, tflc)
    ]

    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER', verbose=True)
    sumo_ctl.add(UC03bVlcController(mnwf_nodes[0]))
    sumo_ctl.add(DataRecorder(mnwf_nodes[0], f'{project_path}/output'))
    sumo_ctl.add(UC03bVlcController(mnwf_nodes[1]))
    sumo_ctl.add(DataRecorder(mnwf_nodes[1], f'{project_path}/output'))
    sumo_ctl.add(UC03bTfclController(mnwf_nodes[2]))

    sumo_ctl.setDaemon(True)
    sumo_ctl.start()

    cli = MnwfCli(net)
    cli.start()
    cli.join()

