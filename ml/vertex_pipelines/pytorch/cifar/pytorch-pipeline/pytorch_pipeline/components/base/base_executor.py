import abc
from six import with_metaclass


class BaseExecutor(with_metaclass(abc.ABCMeta, object)):

    def __init__(self):
        pass

    @abc.abstractmethod
    def Do(self, model_class, data_module_class=None, data_module_args=None, module_file_args=None):
        pass