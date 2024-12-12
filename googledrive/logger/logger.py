from ..singleton import Singleton
from ..colors import Color
import datetime
import logging
import pytz
import sys

class LoggerFormatter(logging.Formatter):

    @staticmethod
    def __format__(color: callable):
        return  ( Color.grey("[%(asctime)s] ") 
                + color("[%(levelname)s] ") 
                + Color.yellow("[%(name)s] ") 
                + "%(message)s "
                )

    FORMATS = {
        logging.DEBUG: \
            __format__(Color.green),

        logging.INFO: \
            __format__(Color.blue),

        logging.WARNING: \
            __format__(Color.red),

        logging.ERROR: \
            __format__(Color.red_bright),

        logging.CRITICAL: \
            __format__(Color.red_bright)
    }

    @staticmethod
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        tzinfo = pytz.timezone('America/Argentina/Buenos_Aires')
        return tzinfo.localize(dt)

    def formatTime(self, record, datefmt=None):
        dt = LoggerFormatter.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec='milliseconds')
            except TypeError:
                s = dt.isoformat()
        return s

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%H:%M:%S")
        return formatter.format(record)

import tqdm

class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)  

class LoggerFactory(Singleton):
    def __init__(self, default_logging_level):
        self.default_logging_level = default_logging_level
        self.loggermap = dict()

    def getLogger(self, name, logging_level=None) -> logging.Logger:
        if name in self.loggermap:
            return self.loggermap[name]
        
        if isinstance(logging_level, str):
            try:
                logging_level = getattr(logging, logging_level)
            except Exception as ex:
                print('Invalid logging level, using default level.')
                logging_level = None

        if not logging_level:
            logging_level = self.default_logging_level
        

        logger = logging.getLogger(name)
        handler = TqdmLoggingHandler(logging_level)
        handler.setFormatter(LoggerFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging_level)

        self.loggermap[name] = logger
        return logger
    
def inject_logger(name_or_cls):
    """Decorador para el reemplazo sintáctico de 'log = LoggerFactory.getLogger(...)' """
    if isinstance(name_or_cls, str):
        def wrapper(cls):
            class NewClass(cls):
                __logger__ = None
                #log = LoggerFactory.instance.getLogger(name_or_cls)
                @property
                def log(self):
                    if type(self).__logger__ is None:
                        type(self).__logger__ = \
                            LoggerFactory.instance.getLogger(name_or_cls)
                    
                    return type(self).__logger__

            NewClass.__name__ = cls.__name__
            return NewClass

        return wrapper
    else:
        class NewClass(name_or_cls):
            __logger__ = None
            #log = LoggerFactory.instance.getLogger(name_or_cls.__name__)
            @property
            def log(self):
                if type(self).__logger__ is None:
                    type(self).__logger__ = \
                        LoggerFactory.instance.getLogger(name_or_cls.__name__)
                
                return type(self).__logger__
        NewClass.__name__ = name_or_cls.__name__
        return NewClass
    
import inspect
import warnings

def debug_print(x, *args, **kwargs):
    """
    Función mágica: Si se lo llama dentro
    de una instancia de una clase y 'log'
    está definido y no es nulo, lo usa
    para imprimir un mensaje en el nivel de
    DEBUG. Para poder determinar estas
    condiciones, inspecciona el frame
    actual desde el que fue ejecutada.
    """
    current_frame = inspect.currentframe()
    
    caller_frame = current_frame.f_back
    
    if not 'self' in caller_frame.f_locals:
        warnings.warn('Instance not found in current context.')
        return
    
    self = caller_frame.f_locals['self']
    
    if not 'log' in dir(self):
        warnings.warn("'log' not found or not defined in current instance.")
        return
    
    log = self.log
    
    if log is None:
        warnings.warn("'log' was found but was None.")
        return
    
    log.debug(x, *args, **kwargs)