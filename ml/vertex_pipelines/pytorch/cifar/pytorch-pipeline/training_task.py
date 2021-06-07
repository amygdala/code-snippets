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
        help="",
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
    # hmmmm
    # args['checkpoint_dir'] = gs_model_path

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
        # dirpath=gs_model_path,
        filename="cifar10_{epoch:02d}",
        save_top_k=1,
        verbose=True,
        monitor="val_loss",
        mode="min",
    )

    if not args["max_epochs"]:
        max_epochs = 2
    else:
        max_epochs = args["max_epochs"]

    # Setting the trainer specific arguments
    trainer_args = {
        "logger": tboard,
        "checkpoint_callback": True,
        "max_epochs": max_epochs,
        "callbacks": [lr_logger, early_stopping, checkpoint_callback],
        "gpus": 1,
        # "accelerator": "ddp",  # with gpus > 1
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

    # aju temp: generalize
    handler = "image_classifier"
    version = "1.0"
    modelpth = Path(os.path.join(args["checkpoint_dir"], args["model_name"]))
    mar_model_name = 'cifar10'

    archive_res = subprocess.run([
        "torch-model-archiver", "--force", "--model-name",  mar_model_name,
        "--serialized-file", modelpth, "--model-file", "pytorch_pipeline/examples/cifar10/cifar10_train.py",
        "--handler", handler, "-v", version, "--export-path", '.'
    ], capture_output=True)
    print('archive command:')
    print(archive_res)

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

    # copy mar file
    marpath = Path(f"./{mar_model_name}.mar")
    if marpath.is_file():  # if file exists
        print('file exists')
    else:
        print('file does not exist')

    import time
    time.sleep(10)


    copyres3 = subprocess.run(
        [
            "/workspace/tools/google-cloud-sdk/bin/gsutil",
            "cp",
            f"{mar_model_name}.mar",
            f"{args['gcs_mar_dir']}/{mar_model_name}.mar",
        ],
        capture_output=True,
    )
    print(copyres3)


