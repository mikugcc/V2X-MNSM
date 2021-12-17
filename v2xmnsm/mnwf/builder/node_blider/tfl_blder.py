from __future__ import annotations

from mn_wifi.node import Car as TrafficLight
from .vlc_blder import VehicleBuilder

class TrafficLightBuilder(VehicleBuilder): 

    def build_node(self) -> TrafficLight:
        return super().build_node()