from v2xmnsm import V2xVehicle
from v2xmnsm.msgs import CAM
from v2xmnsm.sumo import SumoStepListener

UC03B_TFL_PHASES = [
    'ALL_STOP', 
    'BEFORE_VERTICAL_PASS',
    'VERTICAL_PASS', 
    'BEFORE_HORIZONTAL_PASS',
    'HORIZONTAL_PASS'
]

class UC03bVlcController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle):
        super().__init__()
        self.__vlc = v2x_vlc
    
    @property
    def name(self) -> str: 
        return f'{self.__class__.name} :: {self.__vlc.name}'
    
    @SumoStepListener.Substeps(priority=9)
    def sendCAM(self) -> None:
        vlc_cam = CAM(
            from_id = self.__vlc.name, 
            lane = self.__vlc.lane, 
            leader = self.__vlc.get_leader_with_distance()[0], 
            speed = self.__vlc.speed, 
            position = self.__vlc.position, 
            timestamp = self.cur_time
        )
        self.__vlc.broadcast_by_mesh(vlc_cam.to_json())