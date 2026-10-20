# KTC-Easy XYZ Trim

Native KlipperScreen panel for live tool offset trimming on KTC-Easy toolchanger setups.

## Features

- T0–T3 offset tiles and active tool label
- Step sizes 0.01 / 0.05 / 0.10 / 0.50 mm
- Immediate `KTC_OFFSET_ADJUST` commands
- Two-click confirmation for `KTC_OFFSET_SAVE` and `SAVE_CONFIG`
- `SAVE_CONFIG` enabled only when `configfile.save_config_pending` is true

## Requirements

- Klipper with KTC-Easy installed (`KTC_OFFSET_ADJUST`, `KTC_OFFSET_SAVE`)
- KlipperScreen checkout
- Moonraker
- GTK 3 Python bindings (installed automatically if missing)
- [EddySeek](https://github.com/charliemayall/EddySeek) (installed automatically to `~/EddySeek`, required by `xyz calibrate`)
- Config sections in your printer config: `[eddy_seek]`, `[ktc_eddy_calibrate]`, and `[mcu eddy]`. The installer warns if any are missing but does not add them.

On Python older than 3.10 (for example, Bullseye on the BTT CB1), the installer applies a Python 3.9 compatibility patch to the EddySeek checkout.

## Install

git clone https://github.com/buddasticks/klipper-shit.git ~/ktc-xyz-trim
cd ~/ktc-xyz-trim
bash install.sh


If KlipperScreen is not in a standard location:

KS_DIR=/path/to/KlipperScreen bash install.sh


## Uninstall

cd ~/ktc-xyz-trim
bash uninstall.sh


Uninstall leaves EddySeek in place, since other tools may use it.

## What it changes

| File | Change |
|------|--------|
| `<KlipperScreen>/panels/xyz_trim.py` | Panel installed |
| `~/printer_data/config/KlipperScreen.conf` | `[menu __main xyz_trim]` entry added |
| `~/printer_data/config/moonraker.conf` | `[update_manager ktc_xyz_trim]` added (only if `PLUGIN_REPO_URL` is set in `install.sh`) |
| `~/EddySeek` | Cloned and installed via its own `install.sh`; patched for Python 3.9 when needed |

Klipper macros and printer configuration are not modified by this plugin.

## Files

Every file changed is backed up to `~/printer_data/config/.ktc-xyz-trim-backups/` before modification. The 10 most recent backups are kept.

- Install log: `~/printer_data/logs/ktc-xyz-trim.log`
- Install manifest: `~/printer_data/config/.ktc-xyz-trim.manifest`

## Notes

- Adjustments apply immediately. Stage offsets before saving, since `SAVE_CONFIG` restarts Klipper.
- The Python 3.9 patch edits the EddySeek checkout. If you update EddySeek with `git pull`, rerun `bash install.sh` afterwards to reapply it.
- Restart KlipperScreen if it did not restart automatically after install.
