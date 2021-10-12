from mininet.log import setLogLevel, info
from mininet.util import ipAdd
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi, Car as MNCar
from mn_wifi.sumo.runner import sumo
from mn_wifi.link import wmediumd, mesh
from mn_wifi.wmediumdConnector import interference
from utils import SumoControlThread, VlcControlUtil
from traci import StepListener
from abc import ABCMeta, abstractmethod
import subprocess, select, json

class StepController(StepListener, metaclass=ABCMeta):

    def __init__(self, sumo_vlc: VlcControlUtil, mn_host: MNCar) -> None:
        super().__init__() 
        self._sumo_vlc = sumo_vlc
        self._mn_host = mn_host

    @abstractmethod
    def _step_core(self) -> bool: pass

    def step(self, t): 
        expect_step = t if t > 0 else 1
        for _ in range(expect_step): self._step_core()
        return True 

class ObsController(StepController): 
    def __init__(self, sm_car: VlcControlUtil, mn_host: MNCar):
        super().__init__(sm_car, mn_host)

    def _step_core(self):
        out_data = {'FROM': self._mn_host.IP(), 'LANE': self._sumo_vlc.lane_index, 'TYPE': 'OBSTRUCTION DETECTING'}
        self._mn_host.cmd(f"echo -n '{json.dumps(out_data)}' | nc -u -w0 -b 10.255.255.255 8081")
    

class Car1Controller(StepController): 

    def __init__(self, sm_car: VlcControlUtil, mn_host: MNCar):
        super().__init__(sm_car, mn_host)
        self.__rcv_popen = mn_host.popen('nc -luk 8080', shell=True, stdout=-1, stdin=-1)
        self.__rcv_poll = select.poll()
        self.__rcv_poll.register(self.__rcv_popen.stdout,select.POLLIN)

    def _step_core(self):
        if (self.__rcv_poll.poll(1)): 
            in_str = f'[{self.__rcv_popen.readline()}]'
            in_data = json.load(in_str)
            print(f'Vehicle {self._sumo_vlc.name} received a message "{in_data}"')
            obs_lane_index = int(in_data['LANE'])
            self._sumo_vlc.lane_index = obs_lane_index ^ 1 
            in_data['FROM'] = self._mn_host.IP()
            self._mn_host.cmd(f"echo -n '{json.dumps(in_data)}' | nc -u -w0 -b 10.255.255.255 8081")
        else: 
            self._sumo_vlc.lane_index = 1
        return None
    
class Car2Controller(StepController): 

    def __init__(self, sm_car: VlcControlUtil, mn_host: MNCar):
        super().__init__(sm_car, mn_host)
        self.__rcv_popen = mn_host.popen('nc -luk 8081', shell=True, stdout=-1, stdin=-1)
        self.__rcv_poll = select.poll()
        self.__rcv_poll.register(self.__rcv_popen.stdout,select.POLLIN)

    def _step_core(self) :
        if (self.__rcv_poll.poll(1)): 
            in_str = f'[{self.__rcv_popen.readline()}]'
            in_data = json.load(in_str)
            print(f'Vehicle {self._sumo_vlc.name} received a message "{in_data}"')
            obs_lane_index = int(in_data['LANE'])
            self._sumo_vlc.lane_index = obs_lane_index ^ 1 
        else: 
            self._sumo_vlc.lane_index = 1
        return None

class ObsController(StepController): 

    def __init__(self, sumo_vlc: VlcControlUtil, mn_host: MNCar):
        super().__init__(sumo_vlc, mn_host)

    def _step_core(self) -> None:
        return super()._step_core()


def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."
    info("*** Creating nodes\n")
    for i in range(1, 5): 
        net.addCar(f'car{i}', wlans=1, encrypt=['wpa2'])
    net.addStation('sta1', wlans=1, encrypt=['wpa2'], position='100,0,0')
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
        position='100,50,0', range=100, **kwargs
    )
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])

    for id, car in enumerate(net.cars):
        car.setIP('192.168.0.{}/24'.format(id+1),
                  intf='{}'.format(car.wintfs[0].name))

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
    # sumo_ctl.add(Car1Controller(VlcControlUtil(0), net.cars[0]))
    # sumo_ctl.add(Car2Controller(VlcControlUtil(1), net.cars[1]))
    # sumo_ctl.add(ObsController(VlcControlUtil(3), net.cars[3]))

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


