import csv, re, os
from typing import Dict
from datetime import datetime
from ..v2x import V2xVehicle
from ..sumo import SumoStepListener
from .utils import make_dirs

class OneFileDataRecorder(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, out_dir: str):
        super().__init__()
        self.__vlc_records: Dict = {}
        self.__v2x_vlc: V2xVehicle = v2x_vlc
        self.__out_path: str = os.path.join(out_dir, datetime.now().strftime("%b%d-%H%M%S"))

    @property
    def name(self) -> str: 
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'

    def before_listening(self):
        make_dirs(self.__out_path)
        self.__file = open(f'{self.__out_path}/{self.__v2x_vlc.name}.csv', mode='a')
        self.__writer = csv.DictWriter(self.__file, [
                'CAR', 'STEP', 'TIME', 
                'LEADER_AND_DISTANCE', 'DRIVING_DISTANCE', 
                'WIFI_SIGNAL_STRENGTH', 'MESH_SIGNAL_STRENGTH', 
                'DATAGRAM_COUNT', 'BYTES_COUNT', 'WIFI_DATAGRAM', 'MESH_DATAGRAM'
            ])
        self.__writer.writeheader()
        return super().before_listening()

    @SumoStepListener.Substeps(priority=9)
    def __cache_data(self) -> None: 
        self.__vlc_records[self.cur_time] = {
            'STEP': self.cur_step , 
            'TIME': self.cur_time, 
            'CAR' : self.__v2x_vlc.name, 
            'LEADER_AND_DISTANCE': self.__v2x_vlc.get_leader_with_distance(), 
            'DRIVING_DISTANCE': self.__v2x_vlc.distance if self.__v2x_vlc.distance>0 else 'None', 
            'WIFI_SIGNAL_STRENGTH': self.__v2x_vlc.wifi_intf.rssi, 
            'DATAGRAM_COUNT': 0,
            'BYTES_COUNT': 0, 
            'WIFI_DATAGRAM': [],
            'MESH_DATAGRAM': []
        }
        return None


    @SumoStepListener.Substeps(priority=8)
    def __write_data(self) -> None: 
        datagrams_queues = {
            'WIFI_DATAGRAM': self.__v2x_vlc.wifi_datagrams, 
            'MESH_DATAGRAM': self.__v2x_vlc.mesh_datagrams
        }
        new_msg_time = 0.0
        for name, queue in datagrams_queues.items(): 
            pre, cur = None, None
            for _ in range(queue.qsize()): 
                pre, cur = cur, queue.get_nowait()
                rgx_search = re.search('"generated_time": (.+?)}', str(cur))
                if not rgx_search: continue 
                datagram = pre + cur
                generated_time = float(rgx_search.group(1))
                if generated_time > new_msg_time: new_msg_time = generated_time
                if generated_time not in self.__vlc_records: 
                    self.__vlc_records[generated_time] = {name: [], 'DATAGRAM_COUNT': 0, 'BYTES_COUNT': 0}
                vlc_record = self.__vlc_records[generated_time]
                package_str = str(datagram).replace('\n', '').replace('"', "'")
                bytes_count = re.search('length (\d+)', package_str).group(1)
                vlc_record[name].append(package_str)
                vlc_record['DATAGRAM_COUNT'] += 1
                vlc_record['BYTES_COUNT'] += int(bytes_count)

        ensured_times = [key for key in self.__vlc_records.keys() if key < new_msg_time - 1]
        self.__writer.writerows([self.__vlc_records.pop(time) for time in ensured_times])

    def after_listening(self):
        self.__writer.writerows(self.__vlc_records.values())
        self.__file.close()
        return super().after_listening()
