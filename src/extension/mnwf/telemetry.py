from mn_wifi.telemetry import telemetry, parseData
import matplotlib.pyplot as plt

class Telemetry(telemetry): 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start(self, 
        nodes=None, data_type='tx_packets', single=False,
        min_x=0, min_y=0, max_x=100, max_y=100, **kwargs
    ):
        ax, arr = 'axes', ''
        for index, _ in enumerate(nodes, 1): arr += f'ax{index}, ' 
        setattr(self, ax, arr[:-2]) 
        if 'tool' not in kwargs: 
            if data_type == 'position':
                parseData.min_x = min_x
                parseData.min_y = min_y
                parseData.max_x = max_x
                parseData.max_y = max_y
                fig, (self.axes) = plt.subplots(1, 1, figsize=(10, 10))
                fig.canvas.set_window_title('V2X MN-WIFI GRAPH')
                self.axes.set_xlabel('meters')
                self.axes.set_xlabel('meters')
                self.axes.set_xlim([min_x, max_x])
                self.axes.set_ylim([min_y, max_y])
            else:
                if single:
                    fig, (self.axes) = plt.subplots(1, 1, figsize=(10, 4))
                else:
                    fig, (self.axes) = plt.subplots(1, (len(nodes)), figsize=(10, 4))
                fig.canvas.set_window_title('Mininet-WiFi Graph')
        self.nodes = nodes
        parseData(nodes, self.axes, single, data_type=data_type, fig=fig, **kwargs)