import csv, re, os
from datetime import datetime
from typing import Dict
from v2xmnsm import SumoStepListener, V2xVehicle

class DataRecorder(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, out_dir: str):
        super().__init__()
        self.__vlc_records: Dict = {}
        self.__v2x_vlc: V2xVehicle = v2x_vlc
        self.__out_path: str = os.path.join(out_dir, datetime.now().strftime("%b%d-%H%M%S"))

    @property
    def name(self) -> str: 
        return f'{self.__class__.__name__}::{self.__v2x_vlc.name}'

    def before_listening(self):
        cur_dir = '.'
        for subdir in self.__out_path.split('/'): 
            cur_dir += ('/' + subdir)
            if os.path.exists(cur_dir): continue
            os.mkdir(cur_dir, mode=0o766)
            if 'SUDO_UID' not in os.environ: continue 
            uid = int(os.environ['SUDO_UID'])
            gid = int(os.environ['SUDO_GID'])
            os.chown(cur_dir, uid, gid)
            os.chmod(cur_dir, mode=0o766)
        self.__v2x_vlc.wifi_datagrams
        self.__v2x_vlc.mesh_datagrams
        self.__file = open(f'{self.__out_path}/{self.__v2x_vlc.name}.csv', mode='a')
        self.__writer = csv.DictWriter(self.__file, [
                'CAR', 'STEP', 'TIME', 
                'LEADER_AND_DISTANCE', 'DRIVING_DISTANCE', 
                'WIFI_SIGNAL_STRENGTH', 'MESH_SIGNAL_STRENGTH', 
                'DATAGRAM_COUNT','WIFI_DATAGRAM', 'MESH_DATAGRAM'
            ])
        self.__writer.writeheader()
        return super().before_listening()

    @SumoStepListener.SUBSTEP(priority=9)
    def __cache_data(self) -> None: 
        self.__vlc_records[self.cur_time] = {
            'STEP': self.cur_step , 
            'TIME': self.cur_time, 
            'CAR' : self.__v2x_vlc.name, 
            'LEADER_AND_DISTANCE': self.__v2x_vlc.get_leader_with_distance(), 
            'DRIVING_DISTANCE': self.__v2x_vlc.distance if self.__v2x_vlc.distance>0 else 'None', 
            'WIFI_SIGNAL_STRENGTH': self.__v2x_vlc.wifi_intf.rssi, 
            'DATAGRAM_COUNT': 0,
            'WIFI_DATAGRAM': [],
            'MESH_DATAGRAM': []
        }
        return None


    @SumoStepListener.SUBSTEP(priority=8)
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
                datagram = str(pre + cur).replace('\n', '').replace('"', "'")
                generated_time = float(rgx_search.group(1))
                if generated_time > new_msg_time: new_msg_time = generated_time
                if generated_time not in self.__vlc_records: 
                    vlc_record = {name: [], 'DATAGRAM_COUNT': 0}
                    self.__vlc_records[generated_time] = vlc_record
                self.__vlc_records[generated_time][name].append(datagram)
                self.__vlc_records[generated_time]['DATAGRAM_COUNT'] += 1
        ensured_times = [key for key in self.__vlc_records.keys() if key < new_msg_time - 1]
        self.__writer.writerows([self.__vlc_records.pop(time) for time in ensured_times])

    def after_listening(self):
        self.__writer.writerows(self.__vlc_records.values())
        self.__file.close()
        return super().after_listening()
