from v2xmnsm.sumo import SumoStepListener
from v2xmnsm.msgs import DENM, OBSTACLE, json_to_package
from v2xmnsm import V2xVehicle

class UC04Car1Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane: int = 0, init_speed:int=15):
        super().__init__()
        self.__vlc = v2x_vlc
        self.__cur_lane = start_lane
        self.__cur_speed = init_speed
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__vlc.name}'
    
    @SumoStepListener.Substeps(priority=9)
    def __detact_obstruction(self) -> None:
        if self.__cur_speed == 0: return None
        if self.__vlc.distance < 70: return None
        vlc_denm = DENM(
            from_id = self.__vlc.name, 
            event = OBSTACLE, 
            lane = self.__cur_lane, 
            position = self.__vlc.position, 
            timestamp = self.cur_time
        )
        self.__vlc.broadcast_by_mesh(vlc_denm.to_json())
        return None
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        if self.__cur_speed == 0: return None
        for _ in range(self.__vlc.mesh_packages.qsize()): 
            package_str = self.__vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.body.situation.cause != OBSTACLE: continue
            if package.header.from_id != self.__vlc.name: continue 
            self.__cur_speed = 0 if self.__cur_speed < 5 else self.__cur_speed - 5
            print(f'{self.__vlc.name} slow down to {self.__cur_speed}')
        self.__vlc.lane = self.__cur_lane
        return None

    @SumoStepListener.Substeps(priority=1)
    def __update_status(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed
    
class UC04Car2Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane:int=0, init_speed:int=15):
        super().__init__()
        self.__vlc = v2x_vlc
        self.__cur_lane = start_lane
        self.__cur_speed = init_speed
    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__vlc.name}'
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__vlc.mesh_packages.qsize()): 
            package_str = self.__vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            print(package)
            if package.body.situation.cause != OBSTACLE: continue
            if self.__cur_lane != package.body.location.lane: continue
            self.__cur_lane = package.body.location.lane ^ 1
            print(f'{self.__vlc.name} changes lane to {self.__cur_lane}')
        return None
    
    @SumoStepListener.Substeps(priority=1)
    def __update_status(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed

class UC04Car3Controller(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, start_lane:int=0, init_speed:int=15):
        super().__init__()
        self.__vlc = v2x_vlc
        self.__cur_lane = start_lane
        self.__cur_speed = init_speed

    
    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__vlc.name}'
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__vlc.mesh_packages.qsize()): 
            package_str = self.__vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.body.situation.cause != OBSTACLE: continue
            self.__cur_speed += 1
            print(f'{self.__vlc.name} speeds up to {self.__cur_speed}')
        return None

    @SumoStepListener.Substeps(priority=1)
    def __update_status(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed