FROM pytorch/pytorch:latest

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ADD pytorch-pipeline /workspace/pytorch-pipeline

ENV PYTHONPATH /workspace/pytorch-pipeline

WORKDIR /workspace/pytorch-pipeline

ENTRYPOINT /bin/bash
