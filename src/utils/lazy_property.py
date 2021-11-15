class lazy_property(object): 

    def __init__(self, func) -> None:
        self.__func = func

    def __get__(self, obj, obj_type=None):
        value = self.__func(obj)
        setattr(obj, self.__func.__name__, value)
        return value
