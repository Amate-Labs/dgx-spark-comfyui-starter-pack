---
name: comfyui-dgx-spark
description: Install, update, and verify ComfyUI on an NVIDIA DGX Spark with comfyui-dgx-spark, custom node repositories, a dedicated Python environment, and pinned package constraints. Use when preparing or refreshing a Spark ComfyUI checkout.
license: MIT
compatibility: Requires Ubuntu on NVIDIA DGX Spark, Python 3.12, git, network access, and a ComfyUI virtual environment with Spark-compatible PyTorch.
metadata:
  author: Amate Labs
  version: "1.0.0"
---

# ComfyUI on DGX Spark

For ComfyUI setup or refresh requests on a DGX Spark, follow [the workflow](references/workflow.md). Read defaults from [defaults.toml](config/defaults.toml) and use [spark_comfy.py](scripts/spark_comfy.py) for inspection, safe support-repository updates, constrained requirements installs, fresh-process AIMDO checks, launching ComfyUI, and running helper-kit scripts with configured paths.

The skill expects Ubuntu on DGX Spark, Python 3.12, git, network access, an existing ComfyUI checkout, and a Python virtual environment with Spark-compatible PyTorch. It clones the Spark helper kit and starter pack when their checkouts are missing.
