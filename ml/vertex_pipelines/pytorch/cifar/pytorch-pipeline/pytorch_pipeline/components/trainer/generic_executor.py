# Copyright 2021 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pytorch_pipeline.components.base.base_executor import BaseExecutor

class GenericExecutor(BaseExecutor):

    def Do(self, model_class, data_module_class=None, data_module_args=None, module_file_args=None):
        # TODO: Code to train pretrained model
        pass

    def  _GetFnArgs(self):
        pass

