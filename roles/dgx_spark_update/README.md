# dgx_spark_update

Updates configured APT sources with `ansible.builtin.apt`, installs and checks `fwupd`, and applies firmware updates offered by fwupd. Reboot is opt-in.

This does not promise to install NVIDIA DGX OS release bundles shown only in the local DGX updater (`http://localhost:11000/updates`). Review that interface for vendor platform updates that APT/fwupd do not expose.

Defaults are in `defaults/main.yml`. Override `dgx_spark_update_reboot: true` to reboot after changes.
