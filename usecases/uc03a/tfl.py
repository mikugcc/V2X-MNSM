from v2xmnsm import V2xTfcLight
from v2xmnsm.sumo import SumoStepListener
from v2xmnsm.msgs import DENM, CAM, TRFFICLIGHT_RED ,json_to_package

class UC03aTfclController(SumoStepListener): 
    
    def __init__(self, v2x_tfl: V2xTfcLight):
        super().__init__()
        self.__tfl = v2x_tfl

    @property
    def name(self) -> str: 
        return f'{self.__class__.name} :: {self.__tfl.name}'

    @SumoStepListener.Substeps(10)
    def handle_incoming(self):
        mps_queue = self.__tfl.mesh_packages
        for _ in range(mps_queue.qsize()): 
            cur_packet = mps_queue.get()
            cam: CAM = json_to_package(cur_packet)
            if cam.header.from_id == self.__tfl.name: continue
            pkt_lane = cam.body.reference_position.lane
            if pkt_lane == None: continue 
            if 'HORIZONTAL_PASS' not in self.__tfl.phase: 
                self.__tfl.phase = 'BEFORE_HORIZONTAL_PASS'
        return None

    @SumoStepListener.Substeps(9)
    def stop_all(self): 
        if self.__tfl.phase != 'ALL_STOP': return None
        denm = DENM(
            from_id=self.__tfl.name, 
            event=TRFFICLIGHT_RED, 
            lane='None', 
            position=(0,0,0), 
            timestamp=self.cur_time
        )
        self.__tfl.broadcast_by_mesh(denm.to_json())