import inspect
import importlib
from typing import Optional, Dict
from pytorch_pipeline.components.base.base_component import BaseComponent
from pytorch_pipeline.components.trainer.generic_executor import GenericExecutor
from pytorch_pipeline.components.trainer.executor import Executor

class Trainer(BaseComponent):
    def __init__(self,
                 module_file: Optional = None,
                 data_module_file: Optional = None,
                 trainer_fn: Optional = None,
                 run_fn: Optional = None,
                 data_module_args: Optional[Dict] = None,
                 module_file_args: Optional[Dict] = None,
                 trainer_args: Optional[Dict] = None
                 ):
        super(BaseComponent, self).__init__()
        if [bool(module_file), bool(run_fn), bool(trainer_fn)].count(True) != 1:
          raise ValueError(
              "Exactly one of 'module_file', 'trainer_fn', or 'run_fn' must be "
              "supplied.")

        if module_file and data_module_file:
            # Both module file and data module file are present

            model_class = None
            data_module_class = None

            class_module = importlib.import_module(module_file.split(".")[0])
            data_module = importlib.import_module(data_module_file.split(".")[0])

            for cls in inspect.getmembers(class_module, lambda member: inspect.isclass(
                    member) and member.__module__ == class_module.__name__):
                model_class = cls[1]

            for cls in inspect.getmembers(data_module, lambda member: inspect.isclass(
                    member) and member.__module__ == data_module.__name__):
                data_module_class = cls[1]

            print(model_class, data_module_class)

            Executor().Do(
                model_class=model_class,
                data_module_class=data_module_class,
                data_module_args=data_module_args,
                module_file_args=module_file_args,
                trainer_args=trainer_args
            )
        #
        # elif run_fn:
        #     GenericExecutor().Do()
        # elif trainer_fn:
        #     Executor().Do()











