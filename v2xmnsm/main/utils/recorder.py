from io import FileIO
import os, csv, datetime

class CsvRecorder(object):

    def __init__(self, into_file:FileIO) -> None:
        self.__file = open(f'output/uc1.({self.CUR_DATE.strftime("%b%d-%H%M%S")}).csv', mode='a')
        self.__writer = csv.writer(self.__file, delimiter=';')
        self.__writer.writerow([
            'STEP', 'TIME', 'CAR', 
            'LEADER', 'LEADER_DISTANCE', 'DRIVING_DISTANCE', 
            'TCP_DUMP_MSGS', 'SIGNAL_STRENGTH'
        ])
        self.__writer
        return None