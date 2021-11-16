from typing import List
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import mesh as Mesh, wmediumd
from mn_wifi.wmediumdConnector import interference
from extension import *
from message import *
import os, csv, time

class CarController(SumoStepListener): 
    def __init__(self, v2x_vlc: V2xVehicle):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = 0

    def __detact_obstruction(self) -> int: 
        leader, gap_with = self.__v2x_vlc.get_leader_with_distance()
        if (leader != 'obs' or gap_with >= 50): return -1 
        return self.__v2x_vlc.lane_index

    def _step_core(self):
        #HANDLE INCOMING
        while self.__v2x_vlc.received_bcst_stack: 
            in_package = self.__v2x_vlc.received_bcst_stack.pop()
            print(f'RECEIVED {in_package}')
            m_type, m_ip, m_payload = in_package.split('::')
            if m_type == 'CAM' or m_ip == self.__v2x_vlc.wifi_intf.ip: continue
            vlc_denm = DENM.MsgBuilder(str_cmd=m_payload)
            if vlc_denm.behavior == DENM.Behavior.STOP:
                self.__v2x_vlc.stop()
            elif vlc_denm.behavior == DENM.Behavior.CHANGE_TO: 
                self.__cur_lane = vlc_denm.parameters[0]
            info(f'\tNAME: {self.__v2x_vlc.name}\tMSG: {m_payload}\n')
        self.__v2x_vlc.lane_index = self.__cur_lane
        #HANDLE OUTGOING
        vlc_cam = CAM.MsgBuilder(# SEND CAM
            time=SumoControlThread.simulation_time(), 
            position=self.__v2x_vlc.position, 
            speed =self.__v2x_vlc.get_speed(), 
            leader=self.__v2x_vlc.get_leader_with_distance()[0]
        )
        self.__v2x_vlc.broadcast_by_wifi(f'CAM::{self.__v2x_vlc.wifi_intf.ip}::{vlc_cam.serialisation}')
        obs_lane_index = self.__detact_obstruction()
        if(obs_lane_index >= 0): # SEND DENM
            self.__cur_lane = obs_lane_index ^ 1 
            vlc_denm = DENM.MsgBuilder(DENM.Behavior.CHANGE_TO, [self.__cur_lane])
            self.__v2x_vlc.broadcast_by_wifi(f'DENM::{self.__v2x_vlc.wifi_intf.ip}::{vlc_denm.serialisation}')
        self.__v2x_vlc.lane_index = self.__cur_lane
        return None

class DataCapturer(SumoStepListener): 

    def __init__(self, v2x_vlcs: List[V2xVehicle]):
        super().__init__()
        self.__step = 0
        self.__v2x_vlcs = v2x_vlcs
        self.__file = open(f'output/({time.time()}).csv', mode='a')
        self.__writer = csv.writer(self.__file, delimiter=';')
        self.__writer.writerow([
            'STEP', 'TIME', 'CAR', 
            'LEADER', 'LEADER_DISTANCE', 'DRIVING_DISTANCE', 
            'TCP_DUMP_MSGS', 'SIGNAL_STRENGTH'
        ])
        
    
    def _step_core(self) -> bool:
        self.__step += 1
        for v2x_vlc in self.__v2x_vlcs:
            leader_name, leader_distance = v2x_vlc.get_leader_with_distance()
            self.__writer.writerow([
                self.__step, 
                f'{SumoControlThread.simulation_time()}s',
                str(v2x_vlc.name), 
                leader_name if leader_name else "No leader", 
                leader_distance if leader_distance else "No leader", 
                v2x_vlc.distance if v2x_vlc.distance > 0 else "Not initialised", 
                str(v2x_vlc.wifi_datagram_stack), 
                f'{v2x_vlc.wifi_intf.rssi}@{v2x_vlc.wifi_intf.name}'
            ])
            v2x_vlc.wifi_datagram_stack.clear()
        return None

    def __del__(self): 
        self.__file.close()
        super().__del__()


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
    
    for i, mn_car in enumerate(net.cars[1:3], start=1): 
        mn_car.setIP(ip=f'192.168.0.{i}', intf=mn_car.intfNames()[0])
        mn_car.setIP(ip=f'192.168.1.{i}', intf=mn_car.intfNames()[1])

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

    for vlc in vlcs: 
        vlc.wifi_intf.setRange(200)
        vlc.mesh_intf.setRange(1)
    
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_ctl.add(CarController(vlcs[0]))
    sumo_ctl.add(CarController(vlcs[1]))
    #sumo_ctl.add(DataCapturer(vlcs))
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


