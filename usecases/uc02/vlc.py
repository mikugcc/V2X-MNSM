from v2xmnsm import V2xVehicle
from v2xmnsm.sumo import SumoStepListener
from v2xmnsm.msgs import CAM, json_to_package

class UC02CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, speed: int = 13):
        super().__init__()
        self.__cur_lane = 1
        self.__cur_speed = speed
        self.__v2x_vlc = v2x_vlc

    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
        
    @SumoStepListener.Substeps(priority=9)
    def __sendCAM(self) -> None:
        vlc_cam = CAM(
            from_id = self.__v2x_vlc.name, 
            lane = self.__v2x_vlc.lane, 
            leader = self.__v2x_vlc.get_leader_with_distance()[0], 
            speed = self.__v2x_vlc.speed, 
            position = self.__v2x_vlc.position, 
            timestamp = self.cur_time
        )
        self.__v2x_vlc.broadcast_by_mesh(vlc_cam.to_json())

    @SumoStepListener.Substeps(priority=8)
    def __handle_in_cam(self) -> None:
        leader_car, dis_with_leader = self.__v2x_vlc.get_leader_with_distance()
        for _ in range(self.__v2x_vlc.mesh_packages.qsize()): 
            package_str = self.__v2x_vlc.mesh_packages.get_nowait()
            package: CAM = json_to_package(package_str)
            if package.header.from_id != leader_car: continue
            if dis_with_leader >= 75 and self.__cur_speed <= package.body.speed: continue
            self.__cur_lane ^= 1
            print(package)
        return None
    
    @SumoStepListener.Substeps(priority=1)
    def __update_state(self) -> None:
        self.__v2x_vlc.lane = self.__cur_lane
        self.__v2x_vlc.speed = self.__cur_speed
        return None
