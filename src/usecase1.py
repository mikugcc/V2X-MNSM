import os
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi, Car as MNCar
from mn_wifi.sumo.runner import sumo
from mn_wifi.link import wmediumd, mesh
from mn_wifi.wmediumdConnector import interference
from utils import SumoControlThread, VlcControlUtil as SMCar
from utils import IntraVehicleCommunicator as InVlcCommunicator
from traci import StepListener


class VehicleController(StepListener): 

    def __init__(self, sm_car: SMCar, mn_car: MNCar) -> None:
        super().__init__() 
        self.__sumo_car = sm_car
        self.__mnet_car = mn_car
        # dirname = os.path.dirname(os.path.abspath(__file__))
        # script_name = os.path.join(dirname, '/scripts/vlc_uc1.py')
        # mn_car.cmd(f'python {script_name} {mn_car.name} > {mn_car.name}.out &')
        # self.__communicator = InVlcCommunicator(mn_car.name)

    def step(self, t): 
        expect_step = t if t > 0 else 1
        while(expect_step != 0):
            expect_step -= 1
            cons_lane_i = None # self.__communicator.data
            if (cons_lane_i == None): 
                target_lane = 0 if self.__mnet_car.name == 'car1' else 1
                self.__sumo_car.lane_index = target_lane
            else: 
                self.__sumo_car.lane_index = cons_lane_i ^ 1
                # self.__communicator.data = cons_lane_i
    

        

def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)
    "Create a network."
    info("*** Creating nodes\n")
    net.addCar('car1', wlans=2, encrypt=['', 'wpa2'])
    net.addCar('car2', wlans=2, encrypt=['', 'wpa2'])
    net.addCar('car3', wlans=2, encrypt=['', 'wpa2'])
    
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
    sta = net.addStation(
        'sta1', wlans=1, encrypt=['wpa2'], 
        position='500,0,0', range=23
    )

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    for car in net.cars:
        net.addLink(
            car, intf=car.wintfs[1].name, 
            cls=mesh, ssid='meshNet', 
            channel=5, ht_cap='HT40+', range=5
        )
    
    net.addLink(
        sta, intf=sta.wintfs[0].name,
        cls=mesh, ssid='meshNet', channel=5, ht_cap='HT40+'
    )

    info("*** Starting network\n")
    net.build()

    for enb in net.aps:
        enb.start([])

    for id, car in enumerate(net.cars):
        car.setIP(f'192.168.0.{id+1}/24', intf=f'{car.wintfs[1].name}')
        car.setIP(f'192.168.1.{id+1}/24', intf=f'{car.wintfs[0].name}')

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
        extra_params=["--delay 1000"],
        clients=2, exec_order=0
    )

    sumo_ctl = SumoControlThread('SUMO_CAR_CONTROLLER', net)
    for sm_id, mn_car in enumerate(net.cars): 
        car_ctrl = VehicleController(SMCar(sm_id), mn_car)
        sumo_ctl.add(car_ctrl)
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


