
# Workflow Components

This directory contains the definitions of the Argo workflow steps used in the example workflows.  For each step, you can find both the code and the Dockerfile used to build the step's container.

To make it easy to run the examples, we're using prebuilt Docker containers, but if you want to change anything about a step, you can rebuild and use your own container instead.  Just edit the workflow definition under [`samples`](../samples) to point to your own container instead.
