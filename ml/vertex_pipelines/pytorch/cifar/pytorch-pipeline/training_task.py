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
import subprocess
import logging
from pathlib import Path

if __name__ == "__main__":

    logging.getLogger().setLevel(logging.INFO)

    # Argument parser for user defined paths
    parser = ArgumentParser()

    parser.add_argument(
        "--tensorboard_root",
        type=str,
        default="output/tensorboard",
        help="Tensorboard Root path (default: output/tensorboard)",
    )

    parser.add_argument(
        "--gcs_tensorboard_root",
        type=str,
    )

    parser.add_argument(
        "--gcs_tensorboard_instance",
        type=str,
        default="",
    )

    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default="output/train/models",
        help="Path to save model checkpoints (default: output/train/models)",
    )

    parser.add_argument(
        "--gcs_checkpoint_dir",
        type=str,
        help="",
    )

    parser.add_argument(
        "--gcs_mar_dir",
        type=str,
        help="",
    )

    parser.add_argument(
        "--dataset_path",
        type=str,
        default="output/processing",
        help="Cifar10 Dataset path (default: output/processing)",
    )

    parser.add_argument(
        "--gcs_dataset_path",
        type=str,
        help="",
    )

    parser.add_argument(
        "--vertex_num_gpus",
        type=float,
        default=2,
    )
    parser.add_argument(
        "--vertex_max_epochs",
        type=float,
        default=4,
    )

    parser.add_argument(
        "--model_name",
        type=str,
        default="resnet.pth",
        help="Name of the model to be saved as (default: resnet.pth)",
    )

    import sys

    print("sys.argv:")
    print(sys.argv)

    parser = pl.Trainer.add_argparse_args(parent_parser=parser)

    args = vars(parser.parse_args())

    output_pth = args["dataset_path"]
    Path(output_pth).mkdir(parents=True, exist_ok=True)

    gs_dataset_path = args["gcs_dataset_path"]
    gs_model_path = args["gcs_checkpoint_dir"]

    logging.info("gs_dataset_path: %s", gs_dataset_path)
    logging.info("gs_model_path: %s", gs_model_path)

    copyres = subprocess.run(
        [
            "/workspace/tools/google-cloud-sdk/bin/gsutil",
            "cp",
            "-r",
            f"{gs_dataset_path}/*",
            args["dataset_path"],
        ],
        capture_output=True,
    )
    print("gsutil output:")
    print(copyres)

    testres = subprocess.run(
        ["ls", "-lR", args["dataset_path"]], capture_output=True
    )
    print("dataset path listing:")
    print(testres)

    # Enabling Tensorboard Logger, ModelCheckpoint, Earlystopping

    lr_logger = LearningRateMonitor()
    tboard = TensorBoardLogger(args["tensorboard_root"])
    early_stopping = EarlyStopping(
        monitor="val_loss", mode="min", patience=5, verbose=True
    )
    checkpoint_callback = ModelCheckpoint(
        dirpath=args["checkpoint_dir"],
        filename="cifar10_{epoch:02d}",
        save_top_k=1,
        verbose=True,
        monitor="val_loss",
        mode="min",
    )

    num_gpus = int(args["vertex_num_gpus"])
    print(f"num_gpus: {num_gpus}")
    max_epochs = int(args["vertex_max_epochs"])
    print(f"max epochs: {max_epochs}")

    # Set the trainer-specific arguments
    trainer_args = {
        "logger": tboard,
        "profiler": "pytorch",
        "checkpoint_callback": True,
        "max_epochs": max_epochs,
        "callbacks": [lr_logger, early_stopping, checkpoint_callback],
        "gpus": num_gpus,
        # "accelerator": "ddp",  # with gpus > 1
    }
    if num_gpus > 1:
        trainer_args["accelerator"] = "ddp"

    # Set the datamodule specific arguments
    data_module_args = {"train_glob": args["dataset_path"]}

    # Initiate the training process
    trainer = Trainer(
        module_file="cifar10_train.py",
        data_module_file="cifar10_datamodule.py",
        module_file_args=parser,
        data_module_args=data_module_args,
        trainer_args=trainer_args,
    )

    # copy tensorboard logs
    copyres = subprocess.run(
        [
            "/workspace/tools/google-cloud-sdk/bin/gsutil",
            "cp",
            "-r",
            args["tensorboard_root"],
            args["gcs_tensorboard_root"],
        ],
        capture_output=True,
    )
    print(copyres)

    # copy model info
    copyres2 = subprocess.run(
        [
            "/workspace/tools/google-cloud-sdk/bin/gsutil",
            "cp",
            "-r",
            args["checkpoint_dir"],
            gs_model_path,
        ],
        capture_output=True,
    )
    print(copyres2)

    if args["gcs_tensorboard_instance"]:
        try:
            from datetime import datetime

            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            exp_name = f"{args['model_name']}{ts}"
            logging.warning("setting up Vertex tensorboard experiment")
            tb_args = [
                "/opt/conda/bin/tb-gcp-uploader",
                "--tensorboard_resource_name",
                args["gcs_tensorboard_instance"],
                "--logdir",
                args["gcs_tensorboard_root"],
                "--experiment_name",
                exp_name,
                "--one_shot=True",
            ]
            logging.warning("tb args: %s", tb_args)
            tb_res = subprocess.run(tb_args, capture_output=True)
            print(tb_res)
        except Exception as e:
            logging.warning(e)
