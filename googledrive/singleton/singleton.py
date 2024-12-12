from ..properties import classproperty

class SingletonMeta(type):
    """
    Fuente: github.com/datos-Fundar/fundartools
    Metaclase que implementa el patrón de singleton.
    Las clases que la heredan no pueden ser instanciadas más de una vez.
    Provee un método 'get_instance' que es heredado, el cual:
    - Si la clase no está instanciada, la crea.
    - Si está instanciada, la devuelve.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
            return instance

        raise RuntimeError("Class already instantiated. Use get_instance()")

    def get_instance(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
class Singleton(metaclass=SingletonMeta):
    instance: classproperty
    def __init_subclass__(cls) -> None:
        cls.instance = classproperty(lambda _: cls.get_instance())