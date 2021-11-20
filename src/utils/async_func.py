from subprocess import Popen
from threading import Thread
from typing import Callable
from queue import Queue

def async_func(func: Callable):
    def wrapper(*args,**kwargs):
        thr = Thread(target=func,args=args, kwargs=kwargs) 
        thr.setDaemon(True)
        thr.start()
    return wrapper

@async_func
def async_readlines(into_queue: Queue, from_popen:Popen) -> None: 
    for line in iter(from_popen.stdout.readline, b''): 
        if line != None: into_queue.put(line)
    into_queue.put('END OF THE IO')
    from_popen.stdout.close()
    return None
        