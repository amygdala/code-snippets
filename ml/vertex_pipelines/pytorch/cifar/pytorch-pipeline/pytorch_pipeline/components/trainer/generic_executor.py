from pytorch_pipeline.components.base.base_executor import BaseExecutor

class GenericExecutor(BaseExecutor):

    def Do(self, model_class, data_module_class=None, data_module_args=None, module_file_args=None):
        # TODO: Code to train pretrained model
        pass

    def  _GetFnArgs(self):
        pass

