#!/usr/bin/env bash
# KTC-Easy XYZ Trim installer.
# Usage: ./install.sh            (KS_DIR=/path/to/KlipperScreen ./install.sh to override detection)
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PLUGIN_ROOT
# shellcheck source=scripts/lib.sh
source "$PLUGIN_ROOT/scripts/lib.sh"

# Git URL for Moonraker update_manager. Leave empty to skip that step.
PLUGIN_REPO_URL=""

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

install_dependencies() {
  if has_gtk; then
    log "GTK 3 bindings: present"
    return
  fi
  command -v apt-get >/dev/null || die "GTK 3 bindings missing and apt-get is unavailable"
  log "Installing packages: ${APT_DEPS[*]}"
  sudo apt-get update -qq >>"$LOG_FILE" 2>&1 || die "apt update failed, see $LOG_FILE"
  sudo apt-get install -y -qq "${APT_DEPS[@]}" >>"$LOG_FILE" 2>&1 || die "apt install failed, see $LOG_FILE"
  has_gtk || die "GTK 3 bindings still unavailable after install"
  log "GTK 3 bindings: installed"
}

check_ktc_macros() {
  if grep -rqsF --include='*.cfg' 'KTC_OFFSET_ADJUST' "$CONFIG_DIR"; then
    log "KTC-Easy macros: found"
  else
    warn "KTC_OFFSET_ADJUST not found in $CONFIG_DIR; install KTC-Easy before using the panel"
  fi
}

install_panel() {
  local ks_dir="$1" dest="$1/panels/xyz_trim.py"
  if [[ -f "$dest" ]]; then
    backup_file "$dest"
    log "Existing panel backed up"
  fi
  # Compile a staged copy so no __pycache__ lands in either tree.
  cp "$PLUGIN_ROOT/panels/xyz_trim.py" "$STAGE/xyz_trim.py"
  python3 -m py_compile "$STAGE/xyz_trim.py" || die "panel failed to compile"
  install -m 0644 "$STAGE/xyz_trim.py" "$dest"
  log "Panel installed: $dest"
}

register_menu() {
  touch "$KS_CONF"
  if ini_has_section "$KS_CONF" "$MENU_HEADER"; then
    log "KlipperScreen menu entry: already present"
    return
  fi
  backup_file "$KS_CONF"
  printf '\n%s\nname: XYZ Trim\npanel: xyz_trim\n' "$MENU_HEADER" >> "$KS_CONF"
  log "KlipperScreen menu entry: added"
}

register_update_manager() {
  if [[ -z "$PLUGIN_REPO_URL" ]]; then
    log "Moonraker update manager: skipped (PLUGIN_REPO_URL not set)"
    return
  fi
  if [[ ! -d "$PLUGIN_ROOT/.git" ]]; then
    warn "Plugin folder is not a git checkout; skipping update manager"
    return
  fi
  if [[ ! -f "$MOONRAKER_CONF" ]]; then
    warn "moonraker.conf not found; skipping update manager"
    return
  fi
  if ini_has_section "$MOONRAKER_CONF" "$UPDATE_HEADER"; then
    log "Moonraker update manager: already present"
    return
  fi
  backup_file "$MOONRAKER_CONF"
  cat >> "$MOONRAKER_CONF" <<EOF

$UPDATE_HEADER
type: git_repo
path: $PLUGIN_ROOT
origin: $PLUGIN_REPO_URL
primary_branch: main
is_system_service: False
managed_services: KlipperScreen
EOF
  log "Moonraker update manager: added"
}

write_manifest() {
  local ks_dir="$1"
  cat > "$MANIFEST" <<EOF
plugin=$PLUGIN_NAME
version=$PLUGIN_VERSION
installed=$(date -Iseconds)
ks_dir=$ks_dir
panel=$ks_dir/panels/xyz_trim.py
plugin_root=$PLUGIN_ROOT
EOF
  log "Manifest written: $MANIFEST"
}

cleanup() {
  find "$PLUGIN_ROOT" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
  prune_backups
  log "Temporary files cleaned"
}

main() {
  mkdir -p "$LOG_DIR" "$CONFIG_DIR" "$BACKUP_DIR"
  log "=== Installing ${PLUGIN_NAME} v${PLUGIN_VERSION} ==="
  [[ -d "$HOME/klipper" ]] || warn "Klipper not found at ~/klipper; continuing"

  local ks_dir
  ks_dir="$(find_klipperscreen || true)"
  [[ -n "$ks_dir" ]] || die "KlipperScreen checkout not found. Re-run with KS_DIR=/path/to/KlipperScreen"
  log "KlipperScreen: $ks_dir"

  install_dependencies
  check_ktc_macros
  install_panel "$ks_dir"
  register_menu
  register_update_manager
  write_manifest "$ks_dir"
  restart_klipperscreen
  cleanup
  log "=== Done. Open XYZ Trim from the KlipperScreen main menu. ==="
}

main "$@"
