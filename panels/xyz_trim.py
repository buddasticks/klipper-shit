# Native KlipperScreen panel for KTC-Easy Live XYZ Trim.
# Install as panels/xyz_trim.py in the KlipperScreen checkout.

import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from ks_includes.screen_panel import ScreenPanel

LOG = logging.getLogger(__name__)
TOOLS = [f"T{i}" for i in range(4)]
AXES = ("X", "Y", "Z")
STEP_VALUES = (0.01, 0.05, 0.10, 0.50)


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.status = {}
        self.connected = False
        self.busy = False
        self.selected_tool = "T0"
        self.step = 0.01
        self.stage_confirm_tool = None
        self.stage_timeout = None
        self.save_confirm = False
        self.save_timeout = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        root.set_margin_start(8)
        root.set_margin_end(8)
        root.set_margin_top(6)
        root.set_margin_bottom(6)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.connection_label = Gtk.Label(label="Disconnected")
        self.connection_label.set_xalign(0)
        self.active_label = Gtk.Label(label="Active tool: —")
        self.active_label.set_xalign(0)
        top.pack_start(self.connection_label, False, False, 0)
        top.pack_start(self.active_label, False, False, 0)
        root.pack_start(top, False, False, 0)

        heading = Gtk.Label(label="Live XYZ trim — select a tool")
        heading.set_xalign(0)
        root.pack_start(heading, False, False, 0)

        self.tile_grid = Gtk.Grid(column_spacing=6, row_spacing=5)
        self.tool_buttons = {}
        self.tool_labels = {}
        for index, tool in enumerate(TOOLS):
            button = Gtk.Button()
            button.set_hexpand(True)
            button.set_vexpand(False)
            button.set_relief(Gtk.ReliefStyle.NORMAL)
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name = Gtk.Label(label=tool)
            name.set_xalign(0)
            name.get_style_context().add_class("heading")
            values = Gtk.Label(label="X —   Y —   Z —")
            values.set_xalign(0)
            values.set_selectable(False)
            content.pack_start(name, False, False, 0)
            content.pack_start(values, False, False, 0)
            button.add(content)
            button.connect("clicked", self._select_tool, tool)
            self.tile_grid.attach(button, index % 4, index // 4, 1, 1)
            self.tool_buttons[tool] = button
            self.tool_labels[tool] = values
        root.pack_start(self.tile_grid, False, False, 0)

        step_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        step_title = Gtk.Label(label="Step (mm):")
        step_title.set_xalign(0)
        step_row.pack_start(step_title, False, False, 0)
        self.step_buttons = {}
        for value in STEP_VALUES:
            label = f"{value:.2f}"
            button = Gtk.Button(label=label)
            button.connect("clicked", self._select_step, value)
            step_row.pack_start(button, True, True, 0)
            self.step_buttons[value] = button
        root.pack_start(step_row, False, False, 0)

        axis_grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        self.axis_buttons = []
        for col, axis in enumerate(AXES):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            label = Gtk.Label(label=axis)
            label.set_xalign(0.5)
            box.pack_start(label, False, False, 0)
            buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            minus = Gtk.Button(label="−")
            plus = Gtk.Button(label="+")
            for btn, direction in ((minus, -1), (plus, 1)):
                btn.set_hexpand(True)
                btn.connect("clicked", self._adjust_axis, axis, direction)
                buttons.pack_start(btn, True, True, 0)
                self.axis_buttons.append(btn)
            box.pack_start(buttons, False, False, 0)
            axis_grid.attach(box, col, 0, 1, 1)
        root.pack_start(axis_grid, False, False, 0)

        note = Gtk.Label(label="Adjustments apply immediately. Stage offsets before saving; SAVE_CONFIG restarts Klipper.")
        note.set_xalign(0)
        note.set_line_wrap(True)
        note.set_max_width_chars(100)
        root.pack_start(note, False, False, 0)

        save_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.stage_button = Gtk.Button(label="Stage offsets")
        self.stage_button.connect("clicked", self._stage_offsets)
        save_row.pack_start(self.stage_button, True, True, 0)
        self.save_button = Gtk.Button(label="SAVE_CONFIG…")
        self.save_button.connect("clicked", self._save_config)
        save_row.pack_start(self.save_button, True, True, 0)
        root.pack_start(save_row, False, False, 0)

        self.message_label = Gtk.Label(label="Waiting for Moonraker…")
        self.message_label.set_xalign(0)
        self.message_label.set_line_wrap(True)
        root.pack_start(self.message_label, False, False, 0)

        self.content = root
        self.content.show_all()
        self._subscribe()
        self._refresh_status()
        self._render()

    def _subscribe(self):
        objects = {
            "toolchanger": None,
            "configfile": ["save_config_pending", "save_config_pending_items"],
        }
        for tool in TOOLS:
            objects[f"tool {tool}"] = [
                "gcode_x_offset", "gcode_y_offset", "gcode_z_offset"
            ]
        try:
            self._screen._ws.send_method("printer.objects.subscribe", {"objects": objects})
        except Exception:
            LOG.exception("Could not subscribe to KTC-Easy tool offsets")

    def _refresh_status(self):
        try:
            data = self._printer.get_printer_status_data() or {}
            self._merge(data)
            self.connected = bool(self._screen.state.connected)
        except Exception:
            LOG.debug("Could not refresh XYZ Trim status", exc_info=True)

    def _merge(self, update):
        if not isinstance(update, dict):
            return
        for name, fields in update.items():
            if isinstance(fields, dict):
                self.status.setdefault(name, {}).update(fields)
            else:
                self.status[name] = fields

    def _active_tool(self):
        tc = self.status.get("toolchanger", {})
        for value in (tc.get("tool_number"), tc.get("current_tool"),
                      tc.get("active_tool"), tc.get("tool")):
            if isinstance(value, int) and value >= 0:
                return f"T{value}"
            if isinstance(value, str):
                value = value.strip()
                if value.isdigit():
                    return f"T{value}"
                if value.startswith("T") and value[1:].isdigit():
                    return value
        return "—"

    def _offset(self, tool, axis):
        obj = self.status.get(f"tool {tool}", {})
        try:
            return float(obj.get(f"gcode_{axis.lower()}_offset"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fmt(value):
        return "—" if value is None else f"{value:.3f}"

    def _render(self):
        self.connected = bool(self._screen.state.connected)
        active = self._active_tool()
        self.connection_label.set_text("Connected" if self.connected else "Disconnected")
        self.active_label.set_text(f"Active tool: {active}")
        for tool in TOOLS:
            values = "   ".join(f"{axis} {self._fmt(self._offset(tool, axis))}" for axis in AXES)
            self.tool_labels[tool].set_text(values)
            self.tool_buttons[tool].set_sensitive(self.connected and not self.busy)
            context = self.tool_buttons[tool].get_style_context()
            if tool == self.selected_tool:
                context.add_class("suggested-action")
            else:
                context.remove_class("suggested-action")
        for value, button in self.step_buttons.items():
            button.set_sensitive(not self.busy)
            context = button.get_style_context()
            if value == self.step:
                context.add_class("suggested-action")
            else:
                context.remove_class("suggested-action")
        for button in self.axis_buttons:
            button.set_sensitive(self.connected and not self.busy)
        self.stage_button.set_sensitive(self.connected and not self.busy)
        pending = bool(self.status.get("configfile", {}).get("save_config_pending", False))
        self.save_button.set_sensitive(self.connected and not self.busy and pending)

    def _select_tool(self, _button, tool):
        self.selected_tool = tool
        self.stage_confirm_tool = None
        self._cancel_stage_timeout()
        self.stage_button.set_label("Stage offsets")
        self._render()
        self.message_label.set_text(f"Selected {tool} for trim.")

    def _select_step(self, _button, value):
        self.step = value
        self._render()
        self.message_label.set_text(f"Adjustment step: {value:.2f} mm")

    def _run_gcode(self, script, description):
        if not self.connected or self.busy:
            return
        try:
            self._screen._ws.send_method("printer.gcode.script", {"script": script})
            self.message_label.set_text(description)
        except Exception as exc:
            LOG.exception("Could not send XYZ Trim command")
            self.message_label.set_text(f"Command failed: {exc}")

    def _adjust_axis(self, _button, axis, direction):
        delta = direction * self.step
        amount = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
        script = f"KTC_OFFSET_ADJUST T={int(self.selected_tool[1:])} {axis}={amount}"
        self._run_gcode(script, f"Adjusting {self.selected_tool} {axis} by {amount} mm…")

    def _cancel_stage_timeout(self):
        if self.stage_timeout is not None:
            GLib.source_remove(self.stage_timeout)
            self.stage_timeout = None

    def _stage_expired(self):
        self.stage_timeout = None
        self.stage_confirm_tool = None
        self.stage_button.set_label("Stage offsets")
        self.message_label.set_text("Stage confirmation expired.")
        return False

    def _stage_offsets(self, _button):
        tool = self.selected_tool
        if self.stage_confirm_tool != tool:
            self._cancel_stage_timeout()
            self.stage_confirm_tool = tool
            self.stage_button.set_label(f"Confirm Stage {tool}")
            self.message_label.set_text(f"Click again within 5 seconds to stage {tool}.")
            self.stage_timeout = GLib.timeout_add_seconds(5, self._stage_expired)
            return
        self._cancel_stage_timeout()
        self.stage_confirm_tool = None
        self.stage_button.set_label("Stage offsets")
        self._run_gcode(f"KTC_OFFSET_SAVE T={int(tool[1:])}", f"Staging offsets for {tool}…")

    def _save_expired(self):
        self.save_timeout = None
        self.save_confirm = False
        self.save_button.set_label("SAVE_CONFIG…")
        self.message_label.set_text("SAVE_CONFIG confirmation expired.")
        return False

    def _save_config(self, _button):
        pending = bool(self.status.get("configfile", {}).get("save_config_pending", False))
        if not pending:
            self.message_label.set_text("No pending configuration changes to save.")
            return
        if not self.save_confirm:
            if self.save_timeout is not None:
                GLib.source_remove(self.save_timeout)
            self.save_confirm = True
            self.save_button.set_label("Confirm SAVE_CONFIG (restart)")
            self.message_label.set_text("Click again within 5 seconds to save and restart Klipper.")
            self.save_timeout = GLib.timeout_add_seconds(5, self._save_expired)
            return
        if self.save_timeout is not None:
            GLib.source_remove(self.save_timeout)
            self.save_timeout = None
        self.save_confirm = False
        self.save_button.set_label("SAVE_CONFIG…")
        self._run_gcode("SAVE_CONFIG", "Saving configuration and restarting Klipper…")

    def process_update(self, action, data):
        if action == "notify_status_update" and isinstance(data, dict):
            self._merge(data)
            self._render()
        elif action == "notify_klippy_disconnected":
            self.connected = False
            self._render()
        elif action == "notify_klippy_ready":
            self.connected = True
            self._refresh_status()
            self._subscribe()
            self._render()

    def activate(self):
        self._refresh_status()
        self._subscribe()
        self._render()

    def deactivation(self):
        self._cancel_stage_timeout()
        if self.save_timeout is not None:
            GLib.source_remove(self.save_timeout)
            self.save_timeout = None
