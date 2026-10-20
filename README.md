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

## Install

```
git clone <your-repo-url> ~/ktc-xyz-trim
cd ~/ktc-xyz-trim
./install.sh
```

If KlipperScreen is not in a standard location:

```
KS_DIR=/path/to/KlipperScreen ./install.sh
```

## Uninstall

```
cd ~/ktc-xyz-trim
./uninstall.sh
```

## What it changes

| File | Change |
|------|--------|
| `<KlipperScreen>/panels/xyz_trim.py` | Panel installed |
| `~/printer_data/config/KlipperScreen.conf` | `[menu __main xyz_trim]` entry added |
| `~/printer_data/config/moonraker.conf` | `[update_manager ktc_xyz_trim]` added (only if `PLUGIN_REPO_URL` is set in `install.sh`) |

Klipper macros and printer configuration are not modified.

## Files

Every file changed is backed up to `~/printer_data/config/.ktc-xyz-trim-backups/` before modification. The 10 most recent backups are kept.

Install log: `~/printer_data/logs/ktc-xyz-trim.log`
Install manifest: `~/printer_data/config/.ktc-xyz-trim.manifest`

## Notes

- Adjustments apply immediately. Stage offsets before saving, since `SAVE_CONFIG` restarts Klipper.
- After install, restart KlipperScreen if it did not restart automatically.
