import os
class IntraVehicleCommunicator(object): 

    def __init__(self, co_key: str) -> None:
        super().__init__()
        file_dirname = os.path.dirname(os.path.realpath(__file__))
        tmp_dir = f'{os.path.dirname(os.path.dirname(file_dirname))}/tmp'
        if(not os.path.exists(tmp_dir)): os.mkdir(tmp_dir)
        fifo_1_path = os.path.join(tmp_dir, f'{co_key}.1.fifo')
        fifo_2_path = os.path.join(tmp_dir, f'{co_key}.2.fifo')
        if(os.path.exists(fifo_1_path) and os.path.exists(fifo_2_path)):
            self.__fifo_read = os.open(fifo_2_path, os.O_RDONLY)
            self.__fifo_write = os.open(fifo_1_path, os.O_SYNC | os.O_WRONLY)
        else: 
            if(os.path.exists(fifo_1_path)): os.remove(fifo_1_path)
            if(os.path.exists(fifo_2_path)): os.remove(fifo_2_path)
            os.mkfifo(fifo_1_path)
            os.mkfifo(fifo_2_path)
            self.__fifo_read = os.open(fifo_2_path, os.O_NONBLOCK | os.O_RDONLY)
            self.__fifo_write = os.open(fifo_1_path, os.O_SYNC | os.O_WRONLY)
        return None

    @property
    def data(self) -> str: 
        return self.__fifo_read.read()

    @data.setter 
    def data(self, val: str) -> None: 
        return self.__fifo_write.write(val, 1024)

    def __del__(self) -> None:
        self.__fifo_read.close()
        self.__fifo_write.close()
