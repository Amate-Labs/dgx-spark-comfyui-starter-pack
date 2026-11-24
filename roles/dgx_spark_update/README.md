# dgx_spark_update

This role upgrades APT packages, installs `fwupd`, and applies firmware updates offered by fwupd. Set `dgx_spark_update_reboot: true` to let Ansible reboot after changes.

Use the DGX updater at `http://localhost:11000/updates` for NVIDIA release bundles that APT or fwupd do not expose. Set role defaults in `defaults/main.yml` or override them in your playbook.
