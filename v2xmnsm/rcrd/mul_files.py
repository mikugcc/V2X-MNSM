import os, re, csv
from functools import reduce
from typing import Any, Dict, List, Set
from datetime import datetime

from ..v2x import V2xVehicle
from ..sumo import SumoStepListener
from ..msgs import json_to_package, CAM, DENM, Package

from .utils import make_dirs


class MultiFileDataRecorder(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, out_dir: str):
        super().__init__()
        self.__vlc: V2xVehicle = v2x_vlc
        self.__pkg_uniquer: Set[int] = set()
        self.__out_path: str = os.path.join(out_dir, datetime.now().strftime("%b%d-%H%M%S"))

    @property
    def name(self) -> str: 
        return f'{self.__class__.__name__}::{self.__vlc.name}'

    def before_listening(self):
        make_dirs(self.__out_path)
        self.__meta_file = open(f'{self.__out_path}/{self.__vlc.name}.meta.csv', mode='a')
        self.__meta_writer = csv.DictWriter(self.__meta_file, [
            'STEP', 'TIME', 
            'DRIVING_DISTANCE', 'LEADER_AND_DISTANCE', 'WIFI_STRENGTH', 
            'CAM_COUNT', 'DENM_COUNT', 'CAM_BYTES', 'DENM_BYTES'
        ])
        self.__meta_writer.writeheader()
        self.__packets_file = open(f'{self.__out_path}/{self.__vlc.name}.pckg.csv', mode='a')
        self.__packets_writer = csv.DictWriter(self.__packets_file, [
            'FROM', 'BYTES', 'PROTOCOL', 'ID', 'GEN_TIME', 'REC_TIME', 'BODY'
        ])
        self.__packets_writer.writeheader()
        return super().before_listening()


    @SumoStepListener.Substeps(priority=9)
    def handle_data(self) -> None: 
        pkg_jsons: List[str] = []
        pkg_jsons += list(self.__vlc.mesh_packages.queue)
        pkg_jsons += list(self.__vlc.wifi_packages.queue)
        self.__cam_pkgs: List[CAM] = []
        self.__denm_pkgs: List[DENM] = []
        for pkg_json in pkg_jsons: 
            hashed_key = hash(pkg_json)
            if hashed_key in self.__pkg_uniquer: continue
            self.__pkg_uniquer.add(hashed_key)
            pkg = json_to_package(pkg_json)
            if pkg.header.from_id == self.__vlc.name: continue
            pkg.bytes = len(pkg_json.encode('utf-8'))
            if pkg.header.proto_type == 'CAM': 
                self.__cam_pkgs.append(pkg)
            else: 
                self.__denm_pkgs.append(pkg)
        return None

    @SumoStepListener.Substeps(priority=8)
    def write_meta(self) -> None: 
        self.__meta_writer.writerow({
            'STEP': self.cur_step, 'TIME': self.cur_time, 
            'WIFI_STRENGTH': self.__vlc.wifi_intf.rssi, 
            'LEADER_AND_DISTANCE': self.__vlc.get_leader_with_distance(), 
            'DRIVING_DISTANCE': self.__vlc.distance if self.__vlc.distance>0 else 'None', 
            'CAM_COUNT': len(self.__cam_pkgs), 
            'DENM_COUNT': len(self.__denm_pkgs), 
            'CAM_BYTES': reduce(lambda s, p: s + p.bytes, self.__cam_pkgs, 0), 
            'DENM_BYTES': reduce(lambda s, p: s + p.bytes, self.__denm_pkgs, 0)
        })
        return None

    @SumoStepListener.Substeps(priority=8)
    def write_pkgs(self) -> None: 
        output_pkgs: List[Dict[str, Any]] = []
        input_pkgs: List[Package] = self.__cam_pkgs + self.__denm_pkgs
        for pkg in input_pkgs: 
            output_pkgs.append({
                'FROM': pkg.header.from_id, 
                'BYTES': pkg.bytes, 
                'PROTOCOL': pkg.header.proto_type, 
                'ID': pkg.header.message_id, 
                'GEN_TIME': pkg.header.generated_time, 
                'REC_TIME': self.cur_time, 
                'BODY': str(pkg.body.to_dict())
            })
        self.__packets_writer.writerows(output_pkgs)
        return None

    def after_listening(self):
        self.__meta_file.close()
        self.__packets_file.close()
        return super().after_listening()
