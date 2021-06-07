import subprocess
import logging
from pathlib import Path

import torchvision
import webdataset as wds
from sklearn.model_selection import train_test_split

logging.getLogger().setLevel(logging.INFO)
# logging.info("Dataset path is: %s", cifar_dataset.path)
output_pth = "output/processing"

Path(output_pth).mkdir(parents=True, exist_ok=True)

trainset = torchvision.datasets.CIFAR10(
    root="./", train=True, download=True
)
testset = torchvision.datasets.CIFAR10(
    root="./", train=False, download=True
)

Path(output_pth + "/train").mkdir(parents=True, exist_ok=True)
Path(output_pth + "/val").mkdir(parents=True, exist_ok=True)
Path(output_pth + "/test").mkdir(parents=True, exist_ok=True)

random_seed = 25
y = trainset.targets
trainset, valset, y_train, y_val = train_test_split(
    trainset,
    y,
    stratify=y,
    shuffle=True,
    test_size=0.2,
    random_state=random_seed,
)

for name in [(trainset, "train"), (valset, "val"), (testset, "test")]:
    with wds.ShardWriter(
        output_pth + "/" + str(name[1]) + "/" + str(name[1]) + "-%d.tar",
        maxcount=1000,
    ) as sink:
        for index, (image, cls) in enumerate(name[0]):
            sink.write(
                {"__key__": "%06d" % index, "ppm": image, "cls": cls}
            )

entry_point = ["ls", "-R", output_pth]
run_code = subprocess.run(entry_point, stdout=subprocess.PIPE)
print(run_code.stdout)
