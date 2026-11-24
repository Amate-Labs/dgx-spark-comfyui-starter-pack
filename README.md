# DGX Spark ComfyUI Starter Pack

[![skills.sh](https://skills.sh/b/Amate-Labs/dgx-spark-comfyui-starter-pack)](https://skills.sh/Amate-Labs/dgx-spark-comfyui-starter-pack)

Two Ansible roles configure a DGX Spark. An Agent Skill guides ComfyUI setup and updates.

## Contents

- `roles/nvidia_gpu_clock_limit`: run `nvidia-smi -lgc 0,2200` once at boot through systemd.
- `roles/dgx_spark_update`: upgrade APT packages and install firmware offered by fwupd.
- `skills/comfyui-dgx-spark`: guide the ComfyUI install, repository refresh, and verification workflow.
- `constraints.txt`: pin the Spark PyTorch stack for ComfyUI package installs.

APT and fwupd can update the packages and firmware their sources expose. For NVIDIA DGX OS releases shown in the local updater at `http://localhost:11000/updates`, use that updater.

## Install Ansible on the controller

Use Python 3.12 or newer. The roles use `ansible.builtin` modules, so `ansible-core` supplies everything they need.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the playbook

If you run Ansible on the Spark, use the included localhost inventory:

```sh
ansible-playbook -i inventory.localhost.ini playbooks/dgx-spark.yml --become --ask-become-pass
```

If you run Ansible from another machine, copy the sample inventory and replace its example address with the Spark's address:

```ini
[dgx_spark]
spark ansible_host=SPARK_IP ansible_user=YOUR_USER
```

```sh
cp inventory.ini.example inventory.ini
# Edit inventory.ini with your Spark's address and SSH user.
ansible-playbook -i inventory.ini playbooks/dgx-spark.yml --become --ask-become-pass
```

Include either role in another playbook to run it on its own. The update role can restart services or require a reboot. Set `dgx_spark_update_reboot: true` to let Ansible reboot after changes.

## Check GPU clock logs

The service runs once at boot. Read its output from the journal:

```sh
systemctl status nvidia-gpu-clock-limit.service
journalctl -b -u nvidia-gpu-clock-limit.service
```

For a live clock and temperature trace, run:

```sh
nvidia-smi --query-gpu=clocks.current.graphics,temperature.gpu --format=csv -l 1
```

## Use the ComfyUI skill

The skill expects an existing ComfyUI checkout and Python venv. It clones or updates the Spark helper kit and this starter pack as needed. Defaults: `~/playground/ComfyUI`, `~/.venv-comfy`, `~/playground/comfyui-dgx-spark`, and `~/playground/dgx-spark-comfyui-starter-pack`. Set `COMFY`, `VENV`, `COMFYUI_DGX_SPARK_ROOT`, or `DGX_SPARK_STARTER_PACK_ROOT` to use other paths.

Install the skill with the [skills CLI](https://www.skills.sh/docs):

```sh
npx skills add Amate-Labs/dgx-spark-comfyui-starter-pack
```
