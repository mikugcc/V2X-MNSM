from subprocess import Popen
from threading import Thread
from typing import IO, Callable, List

def async_func(func: Callable):
    def wrapper(*args,**kwargs):
        thr = Thread(target=func,args=args, kwargs=kwargs) 
        thr.setDaemon(True)
        thr.start()
    return wrapper

@async_func
def async_readlines(into_stack: List[str], popen:Popen) -> None: 
    while popen.poll() is None: 
        for line in iter(popen.stdout.readline, 'b'): 
            if line == b'': break
            if line == None: continue
            into_stack.append(line)
    into_stack.append('END OF THE IO')
    return None
        