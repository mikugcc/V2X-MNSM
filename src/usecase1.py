from typing import List
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi, Car
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from extension import *
from message import *
import os, csv, time

class Car1Controller(CarController): 
    def __init__(self, sumo_vlc: SumoVehicle, mnwf_vlc: MnwfVehicle):
        super().__init__(sumo_vlc, mnwf_vlc)
        self.__cur_lane = 0

    def __detact_obstruction(self) -> int: 
        leader, gap_with = self._sumo_car.get_leader_with_distance()
        if (leader != 'obs' or gap_with >= 50): return -1 
        return self._sumo_car.lane_index

    def _step_core(self):
        obs_lane_index = self.__detact_obstruction()
        if(obs_lane_index >= 0): 
            self.__cur_lane = obs_lane_index ^ 1 
            vlc_denm = DENM.MsgBuilder(type=DENM.Behavior.CHANGE_TO, pars=[self.__cur_lane])
            self._mn_vlc.broadcast(vlc_denm.serialisation)
            info(vlc_denm)
        self._sumo_car.lane_index = self.__cur_lane
    
class Car2Controller(SumoStepListener): 

    def __init__(self, sumo_vlc: SumoVehicle, mnwf_vlc: MnwfVehicle):
        super().__init__(sumo_vlc, mnwf_vlc)
        self.__cur_lane = 0
        self.__msg_queue:List[str] = [] 
    
    @async_func
    def listen_message(self):
        rcv_data = self._mnwf_car.cmd('uc01_recver 192.168.0.2 9090')
        print(f'RECEIVE DATA {rcv_data}')
        self.__msg_queue.append(rcv_data)

    def _step_core(self):
        # If not start new thread there, 
        # There will be an exception from socket 
        if not self._mnwf_car.waiting: self.listen_message()
        while self.__msg_queue:
            vlc_str = self.__msg_queue.pop()
            vlc_cmd = DENM(str_cmd=vlc_str)
            self._sumo_car.message_backup['IN'].append(vlc_cmd)
            if vlc_cmd.type == Type.STOP: 
                self._sumo_car.stop()
            elif vlc_cmd.type == Type.CHANGE_TO: 
                self.__cur_lane = vlc_cmd.parameters[0]
        self._sumo_car.lane_index = self.__cur_lane
        return None

class SumoRecorder(SumoStepListener): 

    def __init__(self, sumo_cars: List[SMCar], wifi_cars: List[MNCar]) -> None:
        super().__init__(None, None)
        self.__step = 0
        self.__all_cars = list(zip(sumo_cars, wifi_cars))
        self.__file = open(f'output/({time.time()}).csv', mode='a')
        self.__writer = csv.writer(self.__file, delimiter=';')
        self.__writer.writerow([
            'STEP', 'TIME', 'CAR', 
            'LEADER', 'LEADER_DISTANCE', 'DRIVING_DISTANCE', 
            'INCOMING_MSG', 'OUTGOING_MSG', 'SIGNAL_STRENGTH'
        ])
        
    
    def _step_core(self) -> bool:
        self.__step += 1
        for sm_car, wf_car in self.__all_cars:
            leader_name, leader_distance = sm_car.get_leader_with_distance()
            self.__writer.writerow([
                self.__step, 
                f'{SumoControlThread.simulation_time()}s',
                str(sm_car.name), 
                leader_name if leader_name else "No leader", 
                leader_distance if leader_distance else "No leader", 
                sm_car.distance if sm_car.distance > 0 else "Not initialised", 
                str(sm_car.message_backup['IN']), str(sm_car.message_backup['OUT']),
                f'{wf_car.wintfs[0].rssi}@{wf_car.wintfs[0].name}'
            ])
            for _, backup in sm_car.message_backup.items(): backup.clear()
        return None

    def __del__(self): 
        self.__file.close()
        super().__del__()


def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."
    info("*** Creating nodes\n")

    for name in ['obs', 'car1', 'car2', 'car3']: 
        net.addCar(name, wlans=1, encrypt=['wpa2'], txpower=40)

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
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])
    
    for i, mn_car in enumerate(net.cars[1:], start=1): 
        mn_car.setIP(ip=f'192.168.0.{i}', intf=mn_car.intfNames()[0])

    # Track the position of the nodes
    nodes = net.cars + net.aps

    net.telemetry(
        nodes=nodes, data_type='position',
        min_x=-50, min_y=-75,
        max_x=250, max_y=150
    )
    
    info("***** Telemetry Initialised\n")
    project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_file_path = os.path.join(project_root_path, 'sumocfg', 'map.uc1.sumocfg')
    net.useExternalProgram(
        program=SumoInvoker, config_file=cfg_file_path,
        port=8813, clients=2, exec_order=0,
        extra_params=['--delay', '1000', '--start', 'false']
    )
    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER')
    sumo_cars = [SMCar('car1'), SMCar('car2')]
    mini_cars = [net.cars[1], net.cars[2]]
    sumo_ctl.add(Car1Controller(sumo_cars[0], mini_cars[0]))
    sumo_ctl.add(Car2Controller(sumo_cars[1], mini_cars[1]))
    sumo_ctl.add(SumoRecorder(sumo_cars, mini_cars))
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


