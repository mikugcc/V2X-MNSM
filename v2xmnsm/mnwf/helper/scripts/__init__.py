from dataclasses import dataclass
import os

script_path = os.path.dirname(__file__)

@dataclass
class exec:
    UDP_RCV = os.path.join(script_path, 'udp_bcs_rcv')
    UDP_SDR = os.path.join(script_path, 'udp_bcs_sdr')