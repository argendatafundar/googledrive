class classproperty(property):
    """Utilidad para crear propiedades de clase"""

    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()