---
name: comfyui-dgx-spark
description: Install, update, and verify ComfyUI on an NVIDIA DGX Spark using comfyui-dgx-spark, nested custom node repositories, a dedicated Python virtual environment, and repository pip constraints. Use when preparing or refreshing a Spark ComfyUI checkout.
license: MIT
compatibility: Requires Ubuntu on NVIDIA DGX Spark, Python 3.12, git, network access, and a working ComfyUI virtual environment with Spark-compatible PyTorch.
metadata:
  author: Amate Labs
  version: "1.0.0"
---

# ComfyUI on DGX Spark

Use this workflow to prepare a Spark ComfyUI installation while preserving local work and diagnosing verification failures. Do not assume that every warning is harmless: classify each failure using the checks below and investigate any unexpected error.

## Paths and environment

Use these defaults for this workstation:

- `VENV=$HOME/.venv-comfy`
- `COMFY=$HOME/playground/ComfyUI`
- `COMFYUI_DGX_SPARK_ROOT=$HOME/playground/comfyui-dgx-spark`
- Constraints file: `../../constraints.txt` relative to this skill directory, or the matching `constraints.txt` in the starter pack repository.

Honor explicit user values for `VENV`, `COMFY`, and `COMFYUI_DGX_SPARK_ROOT`. Export `VENV` and `COMFY` for every command executed from `comfyui-dgx-spark`; its scripts consume those environment variables. Expand `~` to the target user's home directory before passing paths to tools.

Confirm the target is a DGX Spark/GB10 and the checkout and venv paths are the intended ones. Verify `$VENV/bin/python` exists and can import torch, report its version, CUDA version, device name, and compute capability. The installer expects a Spark compatible PyTorch build (the local tested stack documents 2.11+ cu130; the checked-in constraints currently pin 2.13.0+cu130).

## Preserve work and refresh repositories

1. Inspect `git status --short`, the current branch, and remotes in `$COMFY` and `$COMFYUI_DGX_SPARK_ROOT`. Read existing changes before touching either checkout. Do not silently include unrelated edits in an installer stash. If pre-existing uncommitted ComfyUI work cannot be separated safely, stop and explain what needs preserving.
2. Set `COMFY_ROOT=${COMFY_ROOT:-$COMFY}`. Record each direct child Git repository under `$COMFY_ROOT/custom_nodes`. Do not recurse into models, caches, or non-Git directories.
3. From `$COMFYUI_DGX_SPARK_ROOT`, run `install.sh` with exported `VENV` and `COMFY`. The installer is idempotent and applies Spark wheel fixes and version-aware patches; it does not create ComfyUI or install PyTorch.
4. Inspect the resulting diff and untracked files. Confirm each change belongs to the installer before stashing. Save these installer changes, including untracked launcher/patch files, with a clearly named `git stash push --include-untracked` from `$COMFY`.
5. Update the ComfyUI root checkout with `git pull --ff-only`. Then run `git pull --ff-only` separately in every recorded Git repository directly under `$COMFY_ROOT`. If a repository is not on a branch, has divergent history, or cannot fast-forward, stop and report it; do not reset, force, or discard work.
6. Reapply the installer stash with `git stash pop`. Resolve conflicts by comparing the installer patch's intent with the refreshed upstream implementation. Keep upstream changes where a patch is obsolete, and preserve only still-needed Spark changes. Never choose one side wholesale without reviewing the conflict. Run `git status` and inspect the final diff.

## Install Python requirements

Find every `*requirements*.txt` file under `$COMFY` and its `custom_nodes` tree (including `manager_requirements.txt` and node-specific variants). Exclude test-only requirements unless the user requests development/test dependencies. Review each file and its referenced package sources before installing. Use the configured venv's pip and the versioned constraints file for every install:

```sh
"$VENV/bin/python" -m pip install -c /path/to/dgx-spark-comfyui-starter-pack/constraints.txt -r /path/to/requirements.txt
```

Install the root, manager, and each custom-node runtime requirements file. Keep the command in the foreground and inspect failures; do not bypass constraints or ignore an install error. The constraints file pins the Spark PyTorch stack and is the source of truth for this starter pack.

## Verify and launch

Run the scripts from the kit checkout with both variables exported:

```sh
cd "$COMFYUI_DGX_SPARK_ROOT"
VENV="$VENV" COMFY="$COMFY" bash ./verify.sh
```

The verifier's `FAIL` count must be zero. Treat failures such as missing imports, wrong GPU architecture, missing patches, or missing launcher as real and investigate. A known environment-specific report such as `aimdo init(0) failed: FAIL` is not by itself proof of breakage only if `verify.sh` completes with zero failures and its detailed checks show the expected Spark device, torch/CUDA setup, and usable imports. If these conditions do not hold, investigate rather than dismissing the message.

Start the launcher and inspect the whole startup through the server-ready line:

```sh
"$COMFY/run_dgx_spark.sh"
```

The following reports have been observed as non-fatal on this setup only when startup continues to the ComfyUI URL and the process remains running:

- ONNX Runtime GPU device discovery cannot read `/sys/class/drm/card0/device/vendor`.
- `No OpenGL_accelerate module loaded: No module named 'OpenGL_accelerate'`.

If the server does not become ready, a custom node fails to import, inference fails, or the log presents another error, investigate it. Report the evidence and do not label it a red herring based only on a matching phrase.

## Report completion

Summarize the resulting ComfyUI commit and custom node commits, requirements installed, verifier pass/fail summary, server-ready result, and any unresolved warnings. Leave local changes intact and identify any stash that remains unapplied.
