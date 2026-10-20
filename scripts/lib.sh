#!/usr/bin/env bash
# Shared helpers for the KTC-Easy XYZ Trim installer and uninstaller.

PLUGIN_NAME="ktc-xyz-trim"
PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PLUGIN_VERSION="$(cat "$PLUGIN_ROOT/VERSION" 2>/dev/null || echo unknown)"

# Packages required by the panel (GTK 3 bindings). Append extra packages here.
APT_DEPS=(python3-gi gir1.2-gtk-3.0)

# EddySeek: required by xyz calibrate.
EDDYSEEK_REPO="https://github.com/charliemayall/EddySeek.git"
EDDYSEEK_DIR="$HOME/EddySeek"
PY39_PATCH="$PLUGIN_ROOT/scripts/patch_py39.py"

CONFIG_DIR="$HOME/printer_data/config"
LOG_DIR="$HOME/printer_data/logs"
KS_CONF="$CONFIG_DIR/KlipperScreen.conf"
MOONRAKER_CONF="$CONFIG_DIR/moonraker.conf"
MANIFEST="$CONFIG_DIR/.${PLUGIN_NAME}.manifest"
BACKUP_DIR="$CONFIG_DIR/.${PLUGIN_NAME}-backups"
LOG_FILE="$LOG_DIR/${PLUGIN_NAME}.log"

MENU_HEADER="[menu __main xyz_trim]"
UPDATE_HEADER="[update_manager ktc_xyz_trim]"

log()  { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG_FILE"; }
warn() { log "WARN: $*"; }
die()  { log "ERROR: $*"; exit 1; }

# Locate a KlipperScreen checkout. KS_DIR overrides the search.
find_klipperscreen() {
  local d
  for d in "${KS_DIR:-}" "$HOME/KlipperScreen" "$HOME/klipperscreen" "$HOME/buddasticks/KlipperScreen"; do
    if [[ -n "$d" && -d "$d/panels" && -f "$d/screen.py" ]]; then
      printf '%s\n' "$d"
      return 0
    fi
  done
  return 1
}

# True when GTK 3 Python bindings import cleanly.
has_gtk() {
  python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' >/dev/null 2>&1
}

# True when host python3 is at least MAJOR.MINOR. Usage: python_at_least 3 10
python_at_least() {
  python3 -c "import sys; sys.exit(0 if sys.version_info >= ($1, $2) else 1)"
}

# True when an exact header line exists in an ini-style file.
ini_has_section() {
  grep -qxF "$2" "$1" 2>/dev/null
}

# Removes one [section] (header through the next section header) from an ini-style file.
ini_remove_section() {
  local file="$1" header="$2" tmp
  [[ -f "$file" ]] || return 0
  tmp="$(mktemp)"
  awk -v h="$header" '/^\[/{skip = ($0 == h)} !skip' "$file" > "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

# Copies a file into the backup directory with a timestamp suffix.
backup_file() {
  [[ -f "$1" ]] || return 0
  mkdir -p "$BACKUP_DIR"
  cp -a "$1" "$BACKUP_DIR/$(basename "$1").$(date +%Y%m%d-%H%M%S)"
}

# Keeps the 10 newest backups.
prune_backups() {
  [[ -d "$BACKUP_DIR" ]] || return 0
  (cd "$BACKUP_DIR" && ls -1t | tail -n +11 | xargs -r rm -f --)
}

restart_klipperscreen() {
  if systemctl cat KlipperScreen.service >/dev/null 2>&1; then
    if sudo systemctl restart KlipperScreen.service; then
      log "KlipperScreen restarted"
    else
      warn "KlipperScreen restart failed; restart it manually"
    fi
  else
    warn "KlipperScreen.service not found; restart KlipperScreen manually"
  fi
}
