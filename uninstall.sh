#!/usr/bin/env bash
# KTC-Easy XYZ Trim uninstaller. Removes only what install.sh added.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PLUGIN_ROOT
# shellcheck source=scripts/lib.sh
source "$PLUGIN_ROOT/scripts/lib.sh"

main() {
  mkdir -p "$LOG_DIR" "$BACKUP_DIR"
  log "=== Uninstalling ${PLUGIN_NAME} ==="

  local panel=""
  if [[ -f "$MANIFEST" ]]; then
    panel="$(sed -n 's/^panel=//p' "$MANIFEST")"
  else
    warn "No manifest found; locating KlipperScreen by convention"
    local ks_dir
    ks_dir="$(find_klipperscreen || true)"
    if [[ -n "$ks_dir" ]]; then
      panel="$ks_dir/panels/xyz_trim.py"
    fi
  fi

  if [[ -n "$panel" && -f "$panel" ]]; then
    backup_file "$panel"
    rm -f "$panel"
    log "Removed panel: $panel"
  else
    log "Panel: not found, nothing to remove"
  fi

  if ini_has_section "$KS_CONF" "$MENU_HEADER"; then
    backup_file "$KS_CONF"
    ini_remove_section "$KS_CONF" "$MENU_HEADER"
    log "Removed KlipperScreen menu entry"
  fi

  if ini_has_section "$MOONRAKER_CONF" "$UPDATE_HEADER"; then
    backup_file "$MOONRAKER_CONF"
    ini_remove_section "$MOONRAKER_CONF" "$UPDATE_HEADER"
    log "Removed Moonraker update_manager entry"
  fi

  rm -f "$MANIFEST"
  prune_backups
  restart_klipperscreen
  log "=== Uninstalled. KTC-Easy and Klipper macros were not modified. Backups kept in $BACKUP_DIR ==="
}

main "$@"
