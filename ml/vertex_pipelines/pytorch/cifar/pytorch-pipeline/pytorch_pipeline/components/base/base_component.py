import abc
from six import with_metaclass

class BaseComponent(with_metaclass(abc.ABCMeta, object)):
    def __init__(self):
        pass

    @classmethod
    def _validate_component_class(cls):
        # TODO: Spec validation to be done here
        pass