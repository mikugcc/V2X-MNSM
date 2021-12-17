import os

from mn_wifi.link import mesh as Mesh
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

from v2xmnsm import V2xVehicle, DataRecorder
from v2xmnsm.mnwf import MnwfCli, NetBuilder
from v2xmnsm.sumo import SumoInvoker, SumoControlThread

from vlc import *
    
if __name__ == '__main__':
    net_builder = NetBuilder(wmediumd, interference)
    net_builder.propagation_model(model="logDistance", exp=4.5)
    net_builder.new_access_point('e1').opt_args(
        mac='00:00:00:11:00:01', channel='1', mode = 'g',
        ssid='vanet-ssid', passwd='123456789a', encrypt='wpa2', 
        position='100,100,0', failMode='standalone', datapath='user', 
        range=1
    )
    for index, cname in enumerate(['obs', 'car1', 'car2', 'car3'], 1):
        car = net_builder.new_car(cname)
        car.add_intf(
            ip_v4=(f'192.168.0.{index}', 24), 
            protocol=Mesh, ssid='meshNet', 
            channel=5, ht_cap='HT40+', range=50
        )
        car.add_intf(
            ip_v4=(f'192.168.1.{index}', 24), 
            encrypt='wpa2', is_link=False, range=1
        )
    net = net_builder.build()

    net.telemetry(
        nodes=net.cars[1:] + net.aps, 
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
        V2xVehicle('car2', net.cars[2]), 
        V2xVehicle('car3', net.cars[3])
    ]
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER', verbose=True)
    sumo_ctl.add(UC04Car1Controller(vlcs[0], 1))
    sumo_ctl.add(DataRecorder(vlcs[0], f'{project_path}/output'))
    sumo_ctl.add(UC04Car2Controller(vlcs[1], 1))
    sumo_ctl.add(DataRecorder(vlcs[1], f'{project_path}/output'))
    sumo_ctl.add(UC04Car3Controller(vlcs[2], 0))
    sumo_ctl.add(DataRecorder(vlcs[2], f'{project_path}/output'))

    sumo_ctl.setDaemon(True)
    sumo_ctl.start()

    cli = MnwfCli(net)
    cli.start()
    cli.join()