# dgx_spark_update

This role upgrades APT packages, installs `fwupd`, and applies firmware updates offered by fwupd. It installs `needrestart` and sets its APT hook to restart services that need it during package upgrades. Set `dgx_spark_update_restart_services: false` to leave those services for manual restart. Distro exclusions still apply.

Set `dgx_spark_update_reboot: true` to let Ansible reboot after package or firmware changes. Service restarts do not replace a reboot when the kernel or firmware requires one.

Use the DGX updater at `http://localhost:11000/updates` for NVIDIA release bundles that APT or fwupd do not expose. Set role defaults in `defaults/main.yml` or override them in your playbook.
