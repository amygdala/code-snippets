# Copyright 2019 Google Inc. All Rights Reserved.
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

# FROM tensorflow/tensorflow:2.1.0-gpu-py3
FROM tensorflow/tensorflow:2.3.0-gpu

RUN pip install --upgrade pip
RUN pip install keras-tuner google-cloud-storage


ADD build /ml

ENTRYPOINT ["python", "/ml/bw_hptune_standalone.py"]
