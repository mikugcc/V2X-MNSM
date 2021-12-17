from __future__ import annotations
from typing import Dict, Tuple

from v2xmnsm.sumo import SumoStepListener
from v2xmnsm.msgs import DENM, LANE_CHANGING, OBSTACLE, json_to_package
from v2xmnsm import V2xVehicle


class CarCtrller(SumoStepListener): 

    @property
    def name(self) -> str:
        return f'{self.__class__.__name__}::{self.__vlc.name}'

    LANE_CHANGER: Dict[str, int] = {}
    ALL_VEHICLES: Dict[str, V2xVehicle] = {}

    def __init__(self, v2x_vlc: V2xVehicle):
        super().__init__()
        self.__vlc = v2x_vlc
        self.__vlc.next_lane = None
        CarCtrller.ALL_VEHICLES[v2x_vlc.name] = v2x_vlc

    def is_timer_alart(self, to_lane:int) -> bool: 
        if self.__vlc.next_lane != to_lane: return False 
        if self.__vlc.name not in CarCtrller.LANE_CHANGER: return False
        expect_time = CarCtrller.LANE_CHANGER[self.__vlc.name]
        if self.cur_step < expect_time: return False
        CarCtrller.LANE_CHANGER.pop(self.__vlc.name)
        return True
    
    def set_lane_change_timer(self, to_lane: int, time: int) -> None:
        if self.__vlc.name not in CarCtrller.LANE_CHANGER\
            or CarCtrller.LANE_CHANGER[self.__vlc.name] == 0: 
            CarCtrller.LANE_CHANGER[self.__vlc.name] = time + self.cur_step
            self.__vlc.next_lane = to_lane
        # elif self.__vlc.next_lane == to_lane: 
        #     CarCtrller.LANE_CHANGER[self.__vlc.name] = time + self.cur_step
        return None

    def detact_threat_vlcs(self) -> Dict[str, Tuple[int, int, int]]:
        output_vehicles = {}
        for lc_vlc_name, _ in CarCtrller.LANE_CHANGER.items(): 
            lc_vlc = CarCtrller.ALL_VEHICLES[lc_vlc_name]
            if self.__vlc.lane != lc_vlc.next_lane: continue
            dis_to = self.__vlc.distance_to(lc_vlc.position)
            if abs(dis_to) > self.__vlc.safe_gap: continue
            output_vehicles[lc_vlc.name] = self.__vlc.position
        return output_vehicles

class AutoCar01Ctrller(CarCtrller): 

    def __init__(self, v2x_vlc: V2xVehicle, init_lane: int, init_speed: int=15):
        super().__init__(v2x_vlc)
        self.__vlc = v2x_vlc
        self.__cur_lane = init_lane
        self.__cur_speed = init_speed
    
    @SumoStepListener.Substeps(priority=9)
    def __detact_obstruction(self) -> None:
        if self.__vlc.lane != 1: return None
        if self.__vlc.distance < 50: return None
        vlc_denm = DENM(
            from_id = self.__vlc.name, 
            event = OBSTACLE, 
            lane = self.__cur_lane, 
            position = self.__vlc.position, 
            timestamp = self.cur_time
        )
        self.set_lane_change_timer(0, 15)
        self.__vlc.broadcast_by_mesh(vlc_denm.to_json())
        return None
    
    @SumoStepListener.Substeps(priority=8)
    def __handle_in_denm(self) -> None:
        for _ in range(self.__vlc.mesh_packages.qsize()): 
            package_str = self.__vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.header.from_id == self.__vlc.name: continue 
            if package.body.situation.cause != LANE_CHANGING: continue
            dis_to = self.__vlc.distance_to(package.body.location.position) 
            if abs(dis_to) > self.__vlc.safe_gap: continue
            self.__cur_speed += 2
            print(f'{self.__vlc.name} speed up to {self.__cur_speed}')
            self.__cur_lane = package.body.location.lane
        return None

    @SumoStepListener.Substeps(priority=9)
    def __change_lane_after_delay(self) -> None:
        if self.is_timer_alart(self.__vlc.next_lane): 
            self.__cur_lane = self.__vlc.next_lane 
        return None
    
    @SumoStepListener.Substeps(priority=1)
    def __update_conf(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed

class AutoCar03Ctrller(CarCtrller): 

    def __init__(self, v2x_vlc: V2xVehicle, init_lane: int, init_speed: int=15):
        super().__init__(v2x_vlc)
        self.__vlc = v2x_vlc
        self.__cur_lane = init_lane
        self.__cur_speed = init_speed
    
    @SumoStepListener.Substeps(priority=9)
    def __handle_in_denm(self) -> None: 
        for _ in range(self.__vlc.mesh_packages.qsize()): 
            package_str = self.__vlc.mesh_packages.get_nowait()
            package: DENM = json_to_package(package_str)
            if package.header.from_id == self.__vlc.name: continue 
            if package.body.situation.cause != OBSTACLE: continue
            threat_vehicles = self.__vlc.get_possible_threads()
            for t_vlc_name in threat_vehicles: 
                t_vlc = CarCtrller.ALL_VEHICLES[t_vlc_name]
                vlc_denm = DENM(
                    from_id = self.__vlc.name, 
                    event = LANE_CHANGING, 
                    lane = self.__cur_lane, 
                    position = t_vlc.position, 
                    timestamp = self.cur_time
                )
                self.__vlc.broadcast_by_mesh(vlc_denm.to_json())
                if self.__cur_speed > 1: self.__cur_speed -= 2
                else: self.__cur_speed = 1
                print(f'{self.__vlc.name} slow down to {self.__cur_speed}')
                self.set_lane_change_timer(0, 15)
        return None

    @SumoStepListener.Substeps(priority=9)
    def __change_lane_after_delay(self) -> None:
        if self.is_timer_alart(self.__vlc.next_lane): 
            self.__cur_lane = self.__vlc.next_lane
        return None
    
    @SumoStepListener.Substeps(priority=1)
    def __update_conf(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed

class NormalCar02Ctrller(CarCtrller): 

    def __init__(self, v2x_vlc: V2xVehicle, init_lane: int, init_speed: int=15):
        super().__init__(v2x_vlc)
        self.__vlc = v2x_vlc
        self.__cur_lane = init_lane
        self.__cur_speed = init_speed

    @SumoStepListener.Substeps(priority=10)
    def __update_conf(self) -> None: 
        self.__vlc.lane = self.__cur_lane
        self.__vlc.speed = self.__cur_speed
    
