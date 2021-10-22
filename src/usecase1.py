from typing import List
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi, Car as MNCar
from mn_wifi.sumo.runner import sumo
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from utils import SumoControlThread, VlcStepController, VlcControlUtil as SMCar
from utils import VlcCmdType, VlcCommand, async_func
import csv

class Car1Controller(VlcStepController): 
    def __init__(self, sumo_car: SMCar, mnwf_car: MNCar):
        super().__init__(sumo_car, mnwf_car)
        self.__cur_lane = 0

    def __detact_obstruction(self) -> int: 
        leader, gap_with = self._sumo_car.get_leader_with_distance()
        if (leader != '3' or gap_with >= 50): return -1 
        return self._sumo_car.lane_index

    def _step_core(self):
        obs_lane_index = self.__detact_obstruction()
        if(obs_lane_index >= 0): 
            self.__cur_lane = obs_lane_index ^ 1 
            vlc_cmd = VlcCommand(type=VlcCmdType.CHANGE, pars=[self.__cur_lane])
            str_cmd = f'uc01_bcster 10.0.0.2 9090 {vlc_cmd}'.replace('"', '\\"')
            exe_out = self._mnwf_car.cmd(str_cmd)
            self._sumo_car.message_backup.append(('outgoing', str(vlc_cmd)))
            info(exe_out)
        self._sumo_car.lane_index = self.__cur_lane
    
class Car2Controller(VlcStepController): 

    def __init__(self, sm_car: SMCar, mnwf_car: MNCar):
        super().__init__(sm_car, mnwf_car)
        self.__cur_lane = 0
        self.__msg_queue:List[VlcCommand] = [] 
    
    @async_func
    def listen_message(self):
        rcv_data = self._mnwf_car.cmd('uc01_recver 10.0.0.2 9090')
        self.__msg_queue.append(rcv_data)

    def _step_core(self):
        # If not start new thread there, 
        # There will be an exception from socket 
        if not self._mnwf_car.waiting: self.listen_message()
        while self.__msg_queue:
            vlc_str = self.__msg_queue.pop()
            info(f'CAR2 HANDLE COMMAND {vlc_str}')
            vlc_cmd = VlcCommand(str_cmd=str(vlc_str))
            self._sumo_car.message_backup.append(('incoming', str(vlc_cmd)))
            if vlc_cmd.type == VlcCmdType.STOP: 
                self._sumo_car.stop()
            elif vlc_cmd.type == VlcCmdType.CHANGE: 
                self.__cur_lane = vlc_cmd.parameters[0]
        self._sumo_car.lane_index = self.__cur_lane
        return None

class SumoRecorder(VlcStepController): 

    def __init__(self, sumo_cars: List[SMCar], wifi_cars: List[MNCar]) -> None:
        super().__init__(None, None)
        self.__step = 0
        self.__all_cars = list(zip(sumo_cars, wifi_cars))
        self.__file = open('./output.csv', mode='a')
        self.__writer = csv.writer(self.__file, delimiter=',')
        self.__writer.writerow([
            'STEP', 'TIME', 'CAR', 
            'LEADER', 'LEADER_DISTANCE', 'DRIVING_DISTANCE', 
            'MSG_QUEUE', 'SIGNAL'
        ])
        
    
    def _step_core(self) -> bool:
        self.__step += 1
        for sm_car, wf_car in self.__all_cars:
            leader_name, leader_distance = sm_car.get_leader_with_distance()
            self.__writer.writerow([
                self.__step, 
                f'{SumoControlThread.simulation_time()}s',
                f'Vehicle.{sm_car.name}', 
                leader_name if leader_name else "No leader", 
                leader_distance if leader_distance else "No leader", 
                sm_car.distance if sm_car.distance > 0 else "Not initialised", 
                sm_car.message_backup, 
                f'{wf_car.wintfs[0].rssi}@{wf_car.wintfs[0].name}'
            ])
            sm_car.message_backup.clear()
        return None

    def __del__(self): 
        self.__file.close()
        super().__del__()


def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."
    info("*** Creating nodes\n")
    for i in range(1, 5): net.addCar(f'car{i}', wlans=1, encrypt=['wpa2'], txpower=40)
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
        position='100,25,0', txpower=40, **kwargs
    )
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=1.4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])

    # Track the position of the nodes
    nodes = net.cars + net.aps

    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )
    
    info("***** Telemetry Initialised\n")
    net.useExternalProgram(
        program=sumo, port=8813,
        config_file='map.uc1.sumocfg',
        clients=2, 
        exec_order=0,
        extra_params={'-d 1000'}
    )
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_cars = [SMCar('0'), SMCar('1')]
    sumo_ctl.add(Car1Controller(sumo_cars[0], net.cars[0]))
    sumo_ctl.add(Car2Controller(sumo_cars[1], net.cars[1]))
    sumo_ctl.add(SumoRecorder(sumo_cars, net.cars[:2]))
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


