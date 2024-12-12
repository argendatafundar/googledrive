from dataclasses import dataclass
from dataclasses import asdict
from typing import Callable

def Dataclass(**factory_kwargs):
    """
    Esto es un wrapper de 'dataclass', funciona como una 
    fábrica de clases wrappeadas con dataclass.
    Los keyword-arguments van directo al decorador 'dataclass'.
    Además, suma métodos 'from_dict' y 
    'to_dict' que no tiene dataclass por defecto.

    Está diseñado para que las clases lo subclasseen.
    """

    return type('', (), dict(
        __init_subclass__ =  \
            lambda cls, **kwargs: dataclass(cls, **factory_kwargs, **kwargs),

        from_dict =  \
            classmethod(lambda cls, d: cls(**d)),

        to_dict =  \
            lambda self: asdict(self)
    ))