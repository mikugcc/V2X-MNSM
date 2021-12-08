from threading import Thread

class CLI(Thread): 

    def __init__(self, name: str, is_daemon: bool=True) -> None:
        super().__init__(name=name, daemon=is_daemon)

    def start(self) -> None:
        usr_input = None
        while(usr_input != 'exit'): 
            usr_input = input('traci->')
        return None
        
    
        