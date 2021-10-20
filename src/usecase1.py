from typing import List
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi, Car as MNCar
from mn_wifi.sumo.runner import sumo
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from utils import SumoControlThread, VlcStepController, VlcControlUtil as SMCar
from utils import VlcCmdType, VlcCommand
from threading import Thread

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
            info(exe_out)
        self._sumo_car.lane_index = self.__cur_lane
    
class Car2Controller(VlcStepController): 
    def __init__(self, sm_car: SMCar, mnwf_car: MNCar):
        super().__init__(sm_car, mnwf_car)
        self.__cur_lane = 0
        self.__msg_queue:List[VlcCommand] = [] 
        def listener4Car1(queue: List, mn: MNCar): 
            print(f'CAR2 START TO LISTEN')
            in_str = mn.cmd('uc01_recver 10.0.0.2 9090')
            print(f'CAR2 RECEIVE {in_str}')
            vlc_cmd = VlcCommand(str_cmd = in_str)
            queue.append(vlc_cmd)
        self.__listener = Thread(
            name='Car2Handler', 
            target=listener4Car1, 
            args=[self.__msg_queue, self._mnwf_car]
        )  
        self.__is_started = False

    def _step_core(self):
        # If not start new thread there, 
        # There will be an exception from socket 
        if not self.__is_started:
            self.__listener.start()
            self.__is_started = True 
        while self.__msg_queue:
            vlc_cmd = self.__msg_queue.pop()
            print(f'CAR2 HANDLE COMMAND {vlc_cmd}')
            if vlc_cmd.type == VlcCmdType.STOP: 
                self._sumo_car.stop()
            elif vlc_cmd.type == VlcCmdType.CHANGE: 
                self.__cur_lane = vlc_cmd.parameters[0]
        self._sumo_car.lane_index = self.__cur_lane
        return None


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
    sumo_ctl.add(Car1Controller(SMCar('0'), net.cars[0]))
    sumo_ctl.add(Car2Controller(SMCar('1'), net.cars[1]))
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


