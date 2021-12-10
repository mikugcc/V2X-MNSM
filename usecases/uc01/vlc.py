from v2xmnsm.sumo import SumoStepListener
from v2xmnsm.msgs import DENM, OBSTACLE, json_to_package
from v2xmnsm import V2xVehicle

class UC01CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0):
        super().__init__()
        self.__v2x_vlc = v2x_vlc
        self.__cur_lane = start_lane
        self.__package_cache = set()
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'
    
    @SumoStepListener.Substeps(priority=9)
    def __detact_obstruction(self) -> None:
        cur_dis = self.__v2x_vlc.distance
        if 75 <= cur_dis <= 125: 
            vlc_denm = DENM(
                car_id = self.__v2x_vlc.name, 
                event = OBSTACLE, 
                lane = 0, 
                position = self.__v2x_vlc.position, 
                timestamp = self.cur_time
            )
            self.__v2x_vlc.broadcast_by_wifi(vlc_denm.to_json())
        return None
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__v2x_vlc.wifi_packages.qsize()): 
            package_str = self.__v2x_vlc.wifi_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.header.from_car_id == self.__v2x_vlc.name: continue
            if package.body.situation.cause != OBSTACLE: continue
            pkg_unique_id = str(package.body.situation.cause)+ str(package.body.location.position)
            if pkg_unique_id in self.__package_cache: continue
            self.__package_cache.add(pkg_unique_id)
            print(package)
            self.__cur_lane = package.body.location.lane ^ 1
        self.__v2x_vlc.lane = self.__cur_lane
        return None
