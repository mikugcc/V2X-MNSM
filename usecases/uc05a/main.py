import os

from mn_wifi.link import mesh as Mesh
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import V2xVehicle
from v2xmnsm.rcrd import MultiFileDataRecorder
from v2xmnsm.mnwf import MnwfCli, NetBuilder
from v2xmnsm.sumo import SumoInvoker, SumoControlThread

from vlc import *

if __name__ == '__main__':
    net_builder = NetBuilder(wmediumd, interference)
    net_builder.propagation_model(model="logDistance", exp=4.5)
    net_builder.new_access_point('e1').opt_args(
        mac='00:00:00:11:00:01', channel='1', mode = 'g',
        ssid='vanet-ssid', passwd='123456789a', encrypt='wpa2', 
        position='100,25,0', failMode='standalone', datapath='user', 
        range=100
    )
    for index, cname in enumerate(['car1', 'car2', 'car3'], 1):
        car = net_builder.new_car(cname)
        car.add_intf(
            ip_v4=(f'192.168.0.{index}', 24), 
            protocol=Mesh, ssid='meshNet', 
            channel=5, ht_cap='HT40+', range=50
        )
        car.add_intf(
            ip_v4=(f'192.168.1.{index}', 24), 
            encrypt='wpa2', is_link=False, range=100
        )
    net = net_builder.build()

    net.telemetry(
        nodes=net.cars + net.aps, 
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
        V2xVehicle('car1', net.cars[0]), 
        V2xVehicle('car2', net.cars[1]), 
        V2xVehicle('car3', net.cars[2])
    ]
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(MultiFileDataRecorder(vlcs[0], f'{project_path}/output'))
    sumo_ctl.add(AutoCar01Ctrller(vlcs[0], 1, 5))
    sumo_ctl.add(NormalCarCtrller(vlcs[1], 0, 5))
    sumo_ctl.add(MultiFileDataRecorder(vlcs[2], f'{project_path}/output'))
    sumo_ctl.add(AutoCar02Ctrller(vlcs[2], 1, 5))

    sumo_ctl.setDaemon(True)
    sumo_ctl.start()

    cli = MnwfCli(net)
    cli.start()
    cli.join()