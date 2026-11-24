# ComfyUI on DGX Spark workflow

## Paths and prerequisites

Read path and repository defaults from `config/defaults.toml`. The script accepts overrides through `VENV`, `COMFY`, `COMFYUI_DGX_SPARK_ROOT`, and `DGX_SPARK_STARTER_PACK_ROOT`. Honor other user-provided paths too. Export `VENV` and `COMFY` for commands run from `comfyui-dgx-spark`; its scripts read those variables.

Run the read-only inventory before changing anything:

```sh
python3 skills/comfyui-dgx-spark/scripts/spark_comfy.py inspect
```

Review the report. Confirm the target is a DGX Spark/GB10, both checkout and venv paths are correct, and the torch probe reports a Spark-compatible build. The tested stack uses 2.11+ cu130; `constraints.txt` pins 2.13.0+cu130.

Create the ComfyUI checkout and Python virtual environment before using this workflow.

## Get the helper kit and constraints

Run `python3 skills/comfyui-dgx-spark/scripts/spark_comfy.py sync-support` to preview the helper-kit and starter-pack operations. Inspect the paths and origins, then add `--apply` to clone missing checkouts or fast-forward clean checkouts. The script accepts SSH and HTTPS URLs for the same GitHub repository. It stops on a different repository, a dirty checkout, or a non-Git path. Do not resolve these stops by discarding work.

## Refresh ComfyUI and custom nodes

1. Inspect the `$COMFY` branch, remote, and `git status --short`. Read each tracked change and untracked file. Identify user changes, existing Spark patches, and files the installer may create. Preserve all pre-existing changes in a named stash with `git stash push --include-untracked`; do not include ignored files. Record the stash reference and verify its contents with `git stash show --stat --include-untracked`.
2. Set `COMFY_ROOT=${COMFY_ROOT:-$COMFY}`. Record each direct child Git repository under `$COMFY_ROOT/custom_nodes`. Skip models, caches, and non-Git directories.
3. Confirm `$COMFY` is clean. From `$COMFYUI_DGX_SPARK_ROOT`, run `install.sh` with `VENV` and `COMFY` set. The script applies Spark wheel fixes and version-aware ComfyUI patches. It does not install ComfyUI or PyTorch.
4. Inspect the resulting diff and untracked files. Confirm each change came from the installer. Stash those changes separately, including untracked launcher or patch files, with a descriptive `git stash push --include-untracked` message. Record and verify this stash reference.
5. Run `git pull --ff-only` in `$COMFY`, then in each recorded custom node repository. Stop if a repository is detached, divergent, or cannot fast-forward. Do not reset or discard changes.
6. Apply the installer stash in `$COMFY`, then apply the pre-existing changes stash. Review each conflict against the refreshed upstream code. Keep local changes that remain necessary, and remove Spark patches that upstream or the installer now provides. Keep both stashes until you verify the reconciled worktree and final diff; then remove only the stashes you applied successfully. If you cannot preserve or reconcile a change, stop and explain the specific file and conflict.

## Install Python requirements

Run `python3 skills/comfyui-dgx-spark/scripts/spark_comfy.py requirements` to list the constrained pip commands. Review the discovered files and package sources, then add `--apply` to install them. The script excludes test and development requirements, uses the configured venv, and applies the starter-pack `constraints.txt` to every install. Read pip errors and resolve them before moving on. Do not bypass constraints.

## Verify and launch

Run the verifier from the helper kit with both paths set:

```sh
cd "$COMFYUI_DGX_SPARK_ROOT"
VENV="$VENV" COMFY="$COMFY" bash ./verify.sh
```

Investigate failed checks. Some verifier versions call `comfy_aimdo.control.init()` and then call the underlying `c.lib.init(0)` in the same Python process. The second call can return false because AIMDO has already initialized. Check the verifier code before treating that result as an initialization failure.

Test AIMDO in a fresh Python process with:

```sh
python3 skills/comfyui-dgx-spark/scripts/spark_comfy.py aimdo
```

This initializes CUDA, allocates a tensor, then calls the wrapper once. A nonzero result needs investigation.

Confirm the result against ComfyUI's startup log. Look for AIMDO initialized for the NVIDIA GB10 and DynamicVRAM enabled. Investigate if either check fails.

The installer's commit ancestry check can label ComfyUI as legacy when its commit hashes do not appear in that checkout's history. Treat that label as a hint. Record the ComfyUI commit and version, then check startup for async offloading and DynamicVRAM. Report any mismatch between the installer label and runtime behavior.

Launch ComfyUI in an attached terminal with the configured `VENV` and `COMFY` paths:

```sh
python3 skills/comfyui-dgx-spark/scripts/spark_comfy.py launch
```

After confirming startup, stop the process with Ctrl-C in that terminal and confirm it exits. Do not kill processes by name. Leave ComfyUI running only when the user asks.

These reports can be harmless when ComfyUI reaches its URL and stays running:

- ONNX Runtime cannot read `/sys/class/drm/card0/device/vendor` during GPU discovery.
- Python cannot import `OpenGL_accelerate`.

If startup stops, a custom node fails to import, or inference fails, investigate the cause. Treat unfamiliar errors as real until you find evidence otherwise.

## Report the result

Report the ComfyUI and custom node commits, requirements installed, verifier results, server startup, and unresolved warnings. Leave user changes intact and identify any stash that remains unapplied.
