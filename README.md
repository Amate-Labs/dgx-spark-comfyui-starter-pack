# DGX Spark ComfyUI Starter Pack

[![skills.sh](https://skills.sh/b/Amate-Labs/dgx-spark-comfyui-starter-pack)](https://skills.sh/Amate-Labs/dgx-spark-comfyui-starter-pack)

Ansible roles for a DGX Spark, plus an Agent Skill that guides a careful ComfyUI install and refresh.

## Contents

- `roles/nvidia_gpu_clock_limit`: apply `nvidia-smi -lgc 0,2200` once at boot with a systemd oneshot service.
- `roles/dgx_spark_update`: update configured APT packages and available device firmware.
- `skills/comfyui-dgx-spark`: Agent Skills compliant workflow for setting up/updating Spark ComfyUI.
- `constraints.txt`: versioned pip constraints used by the ComfyUI skill (initially copied from the playground).

The firmware role reports pending upgrades and installs them with `fwupdmgr`. This covers firmware exposed through fwupd. The DGX OS web updater at `http://localhost:11000/updates` may deliver NVIDIA platform release bundles beyond APT/fwupd; use that UI when NVIDIA publishes a platform update that is not represented by those package sources.

## Ansible use

Requires Python 3.12+ and an Ubuntu DGX Spark reachable over SSH. The controller requirements install `ansible-core`; these roles use only `ansible.builtin` modules, so no additional Galaxy collections are needed. Set up an isolated controller environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Example inventory:

```ini
[dgx_spark]
spark ansible_host=192.0.2.10 ansible_user=cristian
```

Apply both roles:

```sh
ansible-playbook -i inventory.ini playbooks/dgx-spark.yml --become
```

Use the roles independently by including them in another playbook. The update role's full-upgrade and firmware actions can restart services or require a reboot; rebooting is opt-in (`dgx_spark_update_reboot: true`).

## GPU clock logging

The clock service runs once per boot and leaves its result in the system journal. To inspect it:

```sh
systemctl status nvidia-gpu-clock-limit.service
journalctl -b -u nvidia-gpu-clock-limit.service
```

For a separate live cadence/temperature log, run your existing query when needed:

```sh
nvidia-smi --query-gpu=clocks.current.graphics,temperature.gpu --format=csv -l 1
```

## ComfyUI skill

The skill defaults to `~/playground/comfyui-dgx-spark`, `~/playground/ComfyUI`, and `~/.venv-comfy`. Set `COMFYUI_DGX_SPARK_ROOT`, `COMFY`, or `VENV` to override. Run it with an Agent Skills compatible agent by installing `skills/comfyui-dgx-spark` as a skill.

The skill is published in this repository at `skills/comfyui-dgx-spark` and can be installed with the [skills CLI](https://www.skills.sh/docs):

```sh
npx skills add Amate-Labs/dgx-spark-comfyui-starter-pack
```
