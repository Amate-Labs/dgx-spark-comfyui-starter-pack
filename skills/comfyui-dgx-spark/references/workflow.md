# ComfyUI on DGX Spark workflow

## Paths and prerequisites

Use these defaults:

- `VENV=$HOME/.venv-comfy`
- `COMFY=$HOME/playground/ComfyUI`
- `COMFYUI_DGX_SPARK_ROOT=$HOME/playground/comfyui-dgx-spark`
- `DGX_SPARK_STARTER_PACK_ROOT=$HOME/playground/dgx-spark-comfyui-starter-pack`
- Constraints: `$DGX_SPARK_STARTER_PACK_ROOT/constraints.txt`

Honor user-provided paths. Expand `~` before passing paths to tools. Export `VENV` and `COMFY` for each command run from `comfyui-dgx-spark`; its scripts read those variables.

Confirm the target is a DGX Spark/GB10. Check that `$COMFY` and `$VENV` exist. Verify `$VENV/bin/python` imports torch and report the torch version, CUDA version, device name, and compute capability. The kit expects Spark-compatible PyTorch. The local tested stack uses 2.11+ cu130; this repository's constraints pin 2.13.0+cu130.

Create the ComfyUI checkout and Python virtual environment before using this workflow.

## Get the helper kit and constraints

1. If `$COMFYUI_DGX_SPARK_ROOT` does not exist, clone `https://github.com/Triplany/comfyui-dgx-spark.git` there. If the path exists, confirm it points to that repository. Inspect its branch, remote, and `git status --short`. Read any local changes. Run `git pull --ff-only` only when the worktree is clean and the branch tracks the expected upstream. Stop before updating a dirty or divergent checkout.
2. If `$DGX_SPARK_STARTER_PACK_ROOT/constraints.txt` does not exist, clone `https://github.com/Amate-Labs/dgx-spark-comfyui-starter-pack.git` there. If the checkout exists, inspect its remote and status. Pull with `git pull --ff-only` only when it is clean and tracks the expected repository. Do not overwrite a non-Git directory or dirty checkout.

## Refresh ComfyUI and custom nodes

1. Inspect the `$COMFY` branch, remote, and `git status --short`. Read each tracked change and untracked file. Identify user changes, existing Spark patches, and files the installer may create. Preserve all pre-existing changes in a named stash with `git stash push --include-untracked`; do not include ignored files. Record the stash reference and verify its contents with `git stash show --stat --include-untracked`.
2. Set `COMFY_ROOT=${COMFY_ROOT:-$COMFY}`. Record each direct child Git repository under `$COMFY_ROOT/custom_nodes`. Skip models, caches, and non-Git directories.
3. Confirm `$COMFY` is clean. From `$COMFYUI_DGX_SPARK_ROOT`, run `install.sh` with `VENV` and `COMFY` set. The script applies Spark wheel fixes and version-aware ComfyUI patches. It does not install ComfyUI or PyTorch.
4. Inspect the resulting diff and untracked files. Confirm each change came from the installer. Stash those changes separately, including untracked launcher or patch files, with a descriptive `git stash push --include-untracked` message. Record and verify this stash reference.
5. Run `git pull --ff-only` in `$COMFY`, then in each recorded custom node repository. Stop if a repository is detached, divergent, or cannot fast-forward. Do not reset or discard changes.
6. Apply the installer stash in `$COMFY`, then apply the pre-existing changes stash. Review each conflict against the refreshed upstream code. Keep local changes that remain necessary, and remove Spark patches that upstream or the installer now provides. Keep both stashes until you verify the reconciled worktree and final diff; then remove only the stashes you applied successfully. If you cannot preserve or reconcile a change, stop and explain the specific file and conflict.

## Install Python requirements

Find `*requirements*.txt` files under `$COMFY`, including `manager_requirements.txt` and runtime requirements in custom nodes. Skip test-only files unless the user requests development dependencies. Review package sources before installation. Install each runtime requirements file with the configured venv and the starter pack constraints:

```sh
"$VENV/bin/python" -m pip install \
  -c "$DGX_SPARK_STARTER_PACK_ROOT/constraints.txt" \
  -r /path/to/requirements.txt
```

Install root, manager, and custom node runtime requirements. Read pip errors and resolve them before moving on. Do not bypass constraints. `constraints.txt` pins the Spark PyTorch stack.

## Verify and launch

Run the verifier from the helper kit with both paths set:

```sh
cd "$COMFYUI_DGX_SPARK_ROOT"
VENV="$VENV" COMFY="$COMFY" bash ./verify.sh
```

Investigate failed checks. Some verifier versions call `comfy_aimdo.control.init()` and then call the underlying `c.lib.init(0)` in the same Python process. The second call can return false because AIMDO has already initialized. Check the verifier code before treating that result as an initialization failure.

Test AIMDO in a fresh Python process. Initialize CUDA, allocate a tensor, then call the wrapper once:

```sh
"$VENV/bin/python" - <<'PY'
import torch
torch.cuda.init()
_ = torch.zeros(1, device="cuda")
import comfy_aimdo.control as control
print("AIMDO initialized:", control.init())
PY
```

Confirm the result against ComfyUI's startup log. Look for AIMDO initialized for the NVIDIA GB10 and DynamicVRAM enabled. Investigate if either check fails.

The installer's commit ancestry check can label ComfyUI as legacy when its commit hashes do not appear in that checkout's history. Treat that label as a hint. Record the ComfyUI commit and version, then check startup for async offloading and DynamicVRAM. Report any mismatch between the installer label and runtime behavior.

Launch ComfyUI in an attached terminal and wait for the server URL:

```sh
"$COMFY/run_dgx_spark.sh"
```

After confirming startup, stop the process with Ctrl-C in that terminal and confirm it exits. Do not kill processes by name. Leave ComfyUI running only when the user asks.

These reports can be harmless when ComfyUI reaches its URL and stays running:

- ONNX Runtime cannot read `/sys/class/drm/card0/device/vendor` during GPU discovery.
- Python cannot import `OpenGL_accelerate`.

If startup stops, a custom node fails to import, or inference fails, investigate the cause. Treat unfamiliar errors as real until you find evidence otherwise.

## Report the result

Report the ComfyUI and custom node commits, requirements installed, verifier results, server startup, and unresolved warnings. Leave user changes intact and identify any stash that remains unapplied.
