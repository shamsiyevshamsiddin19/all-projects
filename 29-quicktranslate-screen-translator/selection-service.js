import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

export function getSelection(callback, cancellable) {
    // Faqat belgilangan matn: eski clipboardni tasodifan serverga yubormaymiz.
    let proc;
    try {
        proc = Gio.Subprocess.new(['wl-paste', '--primary', '--no-newline', '--type', 'text'],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
    } catch (e) {
        callback('', 'wl-paste ishga tushmadi.');
        return;
    }
    let timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 2000, () => {
        timeout = 0;
        proc.force_exit();
        return GLib.SOURCE_REMOVE;
    });
    proc.communicate_utf8_async(null, cancellable, (p, res) => {
        let text = '';
        try {
            const [ok, stdout] = p.communicate_utf8_finish(res);
            if (ok && p.get_successful()) text = (stdout || '').trim();
        } catch (e) { proc.force_exit(); }
        if (timeout) GLib.source_remove(timeout);
        if (!cancellable.is_cancelled()) callback(text);
    });
}

export function getTruePointerCoords() {
    try {
        let tracker = Meta.CursorTracker.get_for_display(global.display);
        if (tracker && tracker.get_pointer) {
            let res = tracker.get_pointer();
            if (res) {
                let coords = res[0];
                if (coords && typeof coords.x === 'number' && typeof coords.y === 'number') {
                    if (Number.isFinite(coords.x) && Number.isFinite(coords.y)) {
                        return [Math.round(coords.x), Math.round(coords.y)];
                    }
                }
                if (typeof res[0] === 'number' && typeof res[1] === 'number') {
                    if (Number.isFinite(res[0]) && Number.isFinite(res[1])) {
                        return [Math.round(res[0]), Math.round(res[1])];
                    }
                }
            }
        }
    } catch (e) {
        console.error('[QuickTranslate] Error getting tracker coords:', e);
    }

    try {
        let [x, y] = global.get_pointer();
        if (Number.isFinite(x) && Number.isFinite(y)) return [Math.round(x), Math.round(y)];
    } catch (e) {}

    try {
        let win = global.display ? global.display.get_focus_window() : null;
        if (win) {
            let rect = win.get_frame_rect();
            return [Math.round(rect.x + rect.width / 2), Math.round(rect.y + rect.height / 3)];
        }
    } catch (e) {}

    let mon = Main.layoutManager.primaryMonitor;
    return [Math.round(mon.x + mon.width / 2), Math.round(mon.y + mon.height / 2)];
}
