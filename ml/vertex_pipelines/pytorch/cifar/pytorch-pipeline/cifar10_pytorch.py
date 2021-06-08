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

import pytorch_lightning as pl
import os
from pytorch_pipeline.components.trainer.component import Trainer
# from pytorch_pipeline.components.mar.mar_generation import MarGeneration
from argparse import ArgumentParser
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks import (
    EarlyStopping,
    LearningRateMonitor,
    ModelCheckpoint,
)


# Argument parser for user defined paths
parser = ArgumentParser()

parser.add_argument(
    "--tensorboard_root",
    type=str,
    default="output/tensorboard",
    help="Tensorboard Root path (default: output/tensorboard)",
)

parser.add_argument(
    "--checkpoint_dir",
    type=str,
    default="output/train/models",
    help="Path to save model checkpoints (default: output/train/models)",
)

parser.add_argument(
    "--dataset_path",
    type=str,
    default="output/processing",
    help="Cifar10 Dataset path (default: output/processing)",
)

parser.add_argument(
    "--model_name",
    type=str,
    default="resnet.pth",
    help="Name of the model to be saved as (default: resnet.pth)",
)

parser.add_argument(
    "--minio_path",
    type=str,
    default="tensorboard/version_0",
    help="Path to upload files to minio (default: tensorboard/version_0)",
)

parser = pl.Trainer.add_argparse_args(parent_parser=parser)

args = vars(parser.parse_args())


# Enabling Tensorboard Logger, ModelCheckpoint, Earlystopping

lr_logger = LearningRateMonitor()
tboard = TensorBoardLogger(args["tensorboard_root"])
early_stopping = EarlyStopping(monitor="val_loss", mode="min", patience=5, verbose=True)
checkpoint_callback = ModelCheckpoint(
    dirpath=args["checkpoint_dir"],
    filename="cifar10_{epoch:02d}",
    save_top_k=1,
    verbose=True,
    monitor="val_loss",
    mode="min",
)

if not args["max_epochs"]:
    max_epochs = 1
else:
    max_epochs = args["max_epochs"]


# Setting the trainer specific arguments
trainer_args = {
    "logger": tboard,
    "checkpoint_callback": True,
    "max_epochs": max_epochs,
    "callbacks": [lr_logger, early_stopping, checkpoint_callback],
}


# Setting the datamodule specific arguments
data_module_args = {"train_glob": args["dataset_path"]}


# Initiating the training process
trainer = Trainer(
    module_file="cifar10_train.py",
    data_module_file="cifar10_datamodule.py",
    module_file_args=parser,
    data_module_args=data_module_args,
    trainer_args=trainer_args,
)


# Mar file generation

mar_config = {
    "MODEL_NAME": "cifar10_test",
    "MODEL_FILE": "pytorch_pipeline/examples/cifar10/cifar10_train.py",
    "HANDLER": "image_classifier",
    "SERIALIZED_FILE": os.path.join(args["checkpoint_dir"], args["model_name"]),
    "VERSION": "1",
    "EXPORT_PATH": args["checkpoint_dir"],
    "CONFIG_PROPERTIES": "https://kubeflow-dataset.s3.us-east-2.amazonaws.com/config.properties"
}


# MarGeneration(mar_config=mar_config).generate_mar_file()
