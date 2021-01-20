# Copyright 2020 Google Inc. All Rights Reserved.
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

FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-3:latest

ADD requirements.txt /
# ADD tfdv.py /
RUN pip install -U tensorflow-data-validation
RUN pip download tensorflow_data_validation --no-deps --platform manylinux2010_x86_64 --only-binary=:all:
RUN pip install -U "apache-beam[gcp]"
