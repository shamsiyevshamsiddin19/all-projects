#!/usr/bin/env python3
import os
import subprocess
import threading
import cairo

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

CSS_STYLES = b"""
/* Main Card Container */
.floating-window {
    background-color: transparent;
}

.card-container {
    background-color: rgba(15, 23, 42, 0.95);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 14px 18px;
}

.pill-container {
    background-color: rgba(15, 23, 42, 0.96);
    border-radius: 24px;
    border: 1px solid rgba(56, 189, 248, 0.45);
    padding: 6px 14px;
}

/* Header bar */
.header-box {
    margin-bottom: 8px;
}

.app-title {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
}

.icon-btn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #94a3b8;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 2px 7px;
    font-size: 12px;
}

.icon-btn:hover {
    background-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
}

.icon-btn-danger:hover {
    background-color: #ef4444;
    color: #ffffff;
}

/* Time display */
.time-display {
    color: #38bdf8;
    font-size: 40px;
    font-weight: 800;
    font-family: monospace;
    margin: 4px 0px;
}

.time-display-active {
    color: #38bdf8;
}

.time-display-paused {
    color: #fbbf24;
}

.time-display-done {
    color: #ef4444;
}

.time-pill-text {
    color: #38bdf8;
    font-size: 16px;
    font-weight: 800;
    font-family: monospace;
}

.status-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
}

/* Progress bar */
progressbar.timer-progress trough {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    min-height: 5px;
    border-style: none;
}

progressbar.timer-progress progress {
    background-color: #38bdf8;
    border-radius: 6px;
    min-height: 5px;
}

/* Mode Switcher */
.mode-btn {
    background-color: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
}

.mode-btn.active {
    background-color: rgba(56, 189, 248, 0.22);
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.5);
}

/* Preset pills */
.preset-btn {
    background-color: rgba(255, 255, 255, 0.05);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
}

.preset-btn:hover {
    background-color: rgba(56, 189, 248, 0.25);
    color: #38bdf8;
    border-color: #38bdf8;
}

/* Adjust buttons */
.adj-btn {
    background-color: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 6px;
}

.adj-btn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

/* Primary and secondary control buttons */
.btn-primary {
    background-color: #0284c7;
    color: #ffffff;
    border-radius: 12px;
    border-style: none;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 18px;
}

.btn-primary:hover {
    background-color: #0369a1;
}

.btn-pause {
    background-color: #d97706;
    color: #ffffff;
    border-radius: 12px;
    border-style: none;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 18px;
}

.btn-pause:hover {
    background-color: #b45309;
}

.btn-secondary {
    background-color: rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 14px;
}

.btn-secondary:hover {
    background-color: rgba(255, 255, 255, 0.14);
    color: #ffffff;
}
"""

class FloatingTimerApp:
    def __init__(self):
        # State
        self.mode = "timer"  # "timer" or "stopwatch"
        self.total_seconds = 25 * 60  # Default 25 mins (Pomodoro)
        self.remaining_seconds = 25 * 60
        self.stopwatch_seconds = 0
        self.is_running = False
        self.timer_source_id = None
        self.sound_enabled = True
        self.is_mini = False
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Create GTK Window
        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.win.set_title("Suzuvchi Taymer")
        self.win.set_keep_above(True)       # Always on top
        self.win.stick()                    # Visible across all workspaces
        self.win.set_decorated(False)        # Frameless / Custom sleek UI
        self.win.set_app_paintable(True)
        self.win.set_skip_taskbar_hint(False)
        self.win.set_resizable(False)

        # Transparent visual setup
        screen = self.win.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.win.set_visual(visual)

        # CSS setup
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_STYLES)
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Handle transparent background painting
        self.win.connect("draw", self.on_draw)

        # Enable mouse events for dragging
        self.win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                            Gdk.EventMask.BUTTON_RELEASE_MASK |
                            Gdk.EventMask.POINTER_MOTION_MASK)
        self.win.connect("button-press-event", self.on_window_button_press)

        # Main Layout Stack
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.get_style_context().add_class("floating-window")
        self.win.add(self.main_box)

        # Full Card Container
        self.full_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.full_card.get_style_context().add_class("card-container")
        self.main_box.pack_start(self.full_card, True, True, 0)

        # Mini Pill Container (hidden initially)
        self.mini_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.mini_card.get_style_context().add_class("pill-container")
        self.main_box.pack_start(self.mini_card, True, True, 0)

        self.setup_full_ui()
        self.setup_mini_ui()

        # Keyboard shortcuts
        self.win.connect("key-press-event", self.on_key_press)

        # Position window initially at top right corner
        self.position_top_right()

        self.update_display()
        self.win.show_all()
        self.mini_card.hide()

    def position_top_right(self):
        screen = self.win.get_screen()
        monitor = screen.get_primary_monitor()
        if not monitor:
            monitor = 0
            geom = screen.get_monitor_geometry(0)
        else:
            geom = monitor.get_geometry()
        x = geom.x + geom.width - 320
        y = geom.y + 60
        self.win.move(x, y)

    def on_draw(self, widget, cr):
        # Clear background so RGBA rounded corners render flawlessly without square box artifacts
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def on_window_button_press(self, widget, event):
        if event.button == 1:
            # Native Wayland/X11 drag
            widget.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        return False

    def setup_full_ui(self):
        # 1. Header Bar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.get_style_context().add_class("header-box")

        title_label = Gtk.Label(label="⏱ SUZUVCHI TAYMER")
        title_label.get_style_context().add_class("app-title")
        title_label.set_xalign(0)
        header.pack_start(title_label, True, True, 0)

        # Sound toggle button
        self.sound_btn = Gtk.Button(label="🔊")
        self.sound_btn.get_style_context().add_class("icon-btn")
        self.sound_btn.set_tooltip_text("Ovozni yoqish / o'chirish")
        self.sound_btn.connect("clicked", self.toggle_sound)
        header.pack_start(self.sound_btn, False, False, 0)

        # Mini mode toggle button
        self.mini_btn = Gtk.Button(label="⊡")
        self.mini_btn.get_style_context().add_class("icon-btn")
        self.mini_btn.set_tooltip_text("Ixcham mini-pill rejimiga o'tish")
        self.mini_btn.connect("clicked", lambda _: self.toggle_mini_mode())
        header.pack_start(self.mini_btn, False, False, 0)

        # Close button
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("icon-btn")
        close_btn.get_style_context().add_class("icon-btn-danger")
        close_btn.set_tooltip_text("Yopish")
        close_btn.connect("clicked", lambda _: Gtk.main_quit())
        header.pack_start(close_btn, False, False, 0)

        self.full_card.pack_start(header, False, False, 0)

        # 2. Mode Selector: [Taymer] [Sekundomer]
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.timer_mode_btn = Gtk.Button(label="Taymer")
        self.timer_mode_btn.get_style_context().add_class("mode-btn")
        self.timer_mode_btn.get_style_context().add_class("active")
        self.timer_mode_btn.connect("clicked", lambda _: self.set_mode("timer"))

        self.sw_mode_btn = Gtk.Button(label="Sekundomer")
        self.sw_mode_btn.get_style_context().add_class("mode-btn")
        self.sw_mode_btn.connect("clicked", lambda _: self.set_mode("stopwatch"))

        mode_box.pack_start(self.timer_mode_btn, True, True, 0)
        mode_box.pack_start(self.sw_mode_btn, True, True, 0)
        self.full_card.pack_start(mode_box, False, False, 0)

        # 3. Main Digital Time Display
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.time_label = Gtk.Label(label="25:00")
        self.time_label.get_style_context().add_class("time-display")
        display_box.pack_start(self.time_label, False, False, 0)

        self.status_label = Gtk.Label(label="Pomodoro (Fokus vaqti)")
        self.status_label.get_style_context().add_class("status-label")
        display_box.pack_start(self.status_label, False, False, 0)

        self.full_card.pack_start(display_box, False, False, 0)

        # 4. Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.get_style_context().add_class("timer-progress")
        self.progress_bar.set_fraction(1.0)
        self.full_card.pack_start(self.progress_bar, False, False, 0)

        # 5. Quick Presets Container
        self.preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        presets = [
            ("5d", 5 * 60, "5 daqiqa (Qisqa tanaffus)"),
            ("15d", 15 * 60, "15 daqiqa"),
            ("25d", 25 * 60, "25 daqiqa (Pomodoro)"),
            ("45d", 45 * 60, "45 daqiqa (Dars/Ish)"),
            ("60d", 60 * 60, "1 soat"),
        ]
        for label, sec, desc in presets:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("preset-btn")
            btn.set_tooltip_text(desc)
            btn.connect("clicked", lambda b, s=sec, d=desc: self.apply_preset(s, d))
            self.preset_box.pack_start(btn, True, True, 0)

        self.full_card.pack_start(self.preset_box, False, False, 0)

        # 6. Adjustment Buttons: [-5m] [-1m] [+1m] [+5m]
        self.adj_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        adjustments = [("-5m", -300), ("-1m", -60), ("+1m", 60), ("+5m", 300)]
        for label, delta in adjustments:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("adj-btn")
            btn.connect("clicked", lambda b, d=delta: self.adjust_time(d))
            self.adj_box.pack_start(btn, True, True, 0)

        self.full_card.pack_start(self.adj_box, False, False, 0)

        # 7. Action Controls: [Play / Pause] [Reset]
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.play_btn = Gtk.Button(label="▶ Boshlash")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.play_btn.connect("clicked", self.toggle_start_pause)
        action_box.pack_start(self.play_btn, True, True, 0)

        self.reset_btn = Gtk.Button(label="↺")
        self.reset_btn.get_style_context().add_class("btn-secondary")
        self.reset_btn.set_tooltip_text("Qaytarish (Reset)")
        self.reset_btn.connect("clicked", self.reset_timer)
        action_box.pack_start(self.reset_btn, False, False, 0)

        self.full_card.pack_start(action_box, False, False, 0)

    def setup_mini_ui(self):
        # Mini mode pill UI: [⏱ 24:59] [▶/⏸] [⛶]
        pill_drag_icon = Gtk.Label(label="⏱")
        pill_drag_icon.get_style_context().add_class("time-pill-text")
        self.mini_card.pack_start(pill_drag_icon, False, False, 0)

        self.mini_time_label = Gtk.Label(label="25:00")
        self.mini_time_label.get_style_context().add_class("time-pill-text")
        self.mini_card.pack_start(self.mini_time_label, True, True, 0)

        self.mini_play_btn = Gtk.Button(label="▶")
        self.mini_play_btn.get_style_context().add_class("icon-btn")
        self.mini_play_btn.connect("clicked", self.toggle_start_pause)
        self.mini_card.pack_start(self.mini_play_btn, False, False, 0)

        mini_expand_btn = Gtk.Button(label="⛶")
        mini_expand_btn.get_style_context().add_class("icon-btn")
        mini_expand_btn.set_tooltip_text("Kengaytirish (Full Widget)")
        mini_expand_btn.connect("clicked", lambda _: self.toggle_mini_mode())
        self.mini_card.pack_start(mini_expand_btn, False, False, 0)

    def toggle_mini_mode(self):
        self.is_mini = not self.is_mini
        if self.is_mini:
            self.full_card.hide()
            self.mini_card.show_all()
            self.win.resize(1, 1)  # shrink to mini card size
        else:
            self.mini_card.hide()
            self.full_card.show_all()
            if self.mode == "stopwatch":
                self.preset_box.hide()
                self.adj_box.hide()
                self.progress_bar.hide()
            self.win.resize(1, 1)

    def set_mode(self, new_mode):
        if self.mode == new_mode:
            return
        self.stop_ticker()
        self.mode = new_mode
        if new_mode == "timer":
            self.timer_mode_btn.get_style_context().add_class("active")
            self.sw_mode_btn.get_style_context().remove_class("active")
            self.preset_box.show()
            self.adj_box.show()
            self.progress_bar.show()
            self.status_label.set_text("Taymer")
        else:
            self.sw_mode_btn.get_style_context().add_class("active")
            self.timer_mode_btn.get_style_context().remove_class("active")
            self.preset_box.hide()
            self.adj_box.hide()
            self.progress_bar.hide()
            self.status_label.set_text("Sekundomer")
            self.stopwatch_seconds = 0

        self.is_running = False
        self.play_btn.set_label("▶ Boshlash")
        self.play_btn.get_style_context().remove_class("btn-pause")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.mini_play_btn.set_label("▶")
        self.update_display()

    def apply_preset(self, seconds, description):
        self.stop_ticker()
        self.total_seconds = seconds
        self.remaining_seconds = seconds
        self.status_label.set_text(description)
        self.is_running = False
        self.play_btn.set_label("▶ Boshlash")
        self.play_btn.get_style_context().remove_class("btn-pause")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.mini_play_btn.set_label("▶")
        self.update_display()

    def adjust_time(self, delta):
        if self.mode != "timer":
            return
        new_time = max(10, self.remaining_seconds + delta)
        self.remaining_seconds = new_time
        self.total_seconds = max(self.total_seconds, self.remaining_seconds)
        self.update_display()

    def toggle_sound(self, widget):
        self.sound_enabled = not self.sound_enabled
        self.sound_btn.set_label("🔊" if self.sound_enabled else "🔇")

    def toggle_start_pause(self, widget=None):
        if self.is_running:
            self.pause_ticker()
        else:
            self.start_ticker()

    def start_ticker(self):
        if self.mode == "timer" and self.remaining_seconds <= 0:
            self.remaining_seconds = self.total_seconds if self.total_seconds > 0 else 25 * 60

        self.is_running = True
        self.play_btn.set_label("⏸ To'xtatish")
        self.play_btn.get_style_context().remove_class("btn-primary")
        self.play_btn.get_style_context().add_class("btn-pause")
        self.mini_play_btn.set_label("⏸")

        self.time_label.get_style_context().remove_class("time-display-paused")
        self.time_label.get_style_context().remove_class("time-display-done")
        self.time_label.get_style_context().add_class("time-display-active")

        if self.timer_source_id is None:
            self.timer_source_id = GLib.timeout_add(1000, self.on_tick)

    def pause_ticker(self):
        self.is_running = False
        self.stop_ticker()
        self.play_btn.set_label("▶ Davom etish")
        self.play_btn.get_style_context().remove_class("btn-pause")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.mini_play_btn.set_label("▶")

        self.time_label.get_style_context().remove_class("time-display-active")
        self.time_label.get_style_context().add_class("time-display-paused")

    def stop_ticker(self):
        if self.timer_source_id is not None:
            GLib.source_remove(self.timer_source_id)
            self.timer_source_id = None

    def reset_timer(self, widget=None):
        self.stop_ticker()
        self.is_running = False
        if self.mode == "timer":
            self.remaining_seconds = self.total_seconds
        else:
            self.stopwatch_seconds = 0

        self.play_btn.set_label("▶ Boshlash")
        self.play_btn.get_style_context().remove_class("btn-pause")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.mini_play_btn.set_label("▶")

        self.time_label.get_style_context().remove_class("time-display-active")
        self.time_label.get_style_context().remove_class("time-display-paused")
        self.time_label.get_style_context().remove_class("time-display-done")
        self.update_display()

    def on_tick(self):
        if not self.is_running:
            return False

        if self.mode == "timer":
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.update_display()
                if self.remaining_seconds == 0:
                    self.on_timer_finished()
                    return False
                return True
            else:
                self.on_timer_finished()
                return False
        else:
            # Stopwatch
            self.stopwatch_seconds += 1
            self.update_display()
            return True

    def on_timer_finished(self):
        self.is_running = False
        self.stop_ticker()
        self.play_btn.set_label("▶ Boshlash")
        self.play_btn.get_style_context().remove_class("btn-pause")
        self.play_btn.get_style_context().add_class("btn-primary")
        self.mini_play_btn.set_label("▶")

        self.time_label.get_style_context().remove_class("time-display-active")
        self.time_label.get_style_context().add_class("time-display-done")
        self.status_label.set_text("⏰ Vaqt tugadi!")

        # Sound & Notification
        if self.sound_enabled:
            threading.Thread(target=self.play_alarm_sound, daemon=True).start()

        self.send_system_notification()

    def play_alarm_sound(self):
        # Canberra GTK Play or alarm sound
        sound_paths = [
            "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "/usr/share/sounds/freedesktop/stereo/complete.oga"
        ]
        played = False
        for sp in sound_paths:
            if os.path.exists(sp):
                try:
                    subprocess.run(["canberra-gtk-play", "-f", sp], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    played = True
                    break
                except (subprocess.SubprocessError, OSError):
                    pass
        if not played:
            try:
                subprocess.run(["canberra-gtk-play", "-i", "alarm-clock-elapsed"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (subprocess.SubprocessError, OSError):
                pass

    def send_system_notification(self):
        try:
            subprocess.run([
                "notify-send",
                "-u", "critical",
                "-i", "alarm-symbolic",
                "⏱ Vaqt tugadi!",
                "Belgilangan taymer yakunlandi. Biroz dam oling yoki keyingi ishga o'ting!"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.SubprocessError, OSError):
            pass

    def update_display(self):
        if self.mode == "timer":
            sec = self.remaining_seconds
            total = self.total_seconds
            frac = (sec / total) if total > 0 else 0.0
            self.progress_bar.set_fraction(max(0.0, min(1.0, frac)))
        else:
            sec = self.stopwatch_seconds

        hours = sec // 3600
        mins = (sec % 3600) // 60
        secs = sec % 60

        if hours > 0:
            formatted = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            formatted = f"{mins:02d}:{secs:02d}"

        self.time_label.set_text(formatted)
        self.mini_time_label.set_text(formatted)

    def on_key_press(self, widget, event):
        # Spacebar toggles start/pause
        if event.keyval == Gdk.KEY_space:
            self.toggle_start_pause()
            return True
        # Escape toggles mini mode
        elif event.keyval == Gdk.KEY_Escape:
            self.toggle_mini_mode()
            return True
        return False

def main():
    FloatingTimerApp()
    Gtk.main()

if __name__ == "__main__":
    main()

