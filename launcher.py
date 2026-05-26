"""
launcher.py — Entry point for STARSHIP GALACTIC FRONTIER.
Run: python launcher.py

ONLY this file creates tk.Tk() and calls mainloop().
"""

import math
import random
import tkinter as tk

APP_CONFIG = {"min_w": 1024, "min_h": 768, "default_w": 1280, "default_h": 800}

COLORS = {
    "bg": "#0a0a1a",
    "cyan": "#00f5ff",
    "blue": "#1e90ff",
    "warn": "#ffaa00",
    "danger": "#ff3333",
    "success": "#00ff88",
    "text": "#e0e8ff",
    "muted": "#6a8aaa",
    "panel": "#0d1a2e",
    "panel_hi": "#1a2d4a",
    "panel_active": "#002233",
}


def safe_canvas(canvas, fn, *args, **kwargs):
    try:
        if canvas.winfo_exists():
            return fn(*args, **kwargs)
    except tk.TclError:
        pass
    return None


def defer(parent, callback, *args):
    """Schedule callback on next event-loop tick (never call from destroy handler)."""
    parent.after(0, lambda: callback(*args))


def raise_toplevel(win):
    """Ensure a Toplevel is visible when parent root may be withdrawn."""
    try:
        win.update_idletasks()
        win.deiconify()
        win.lift()
        win.attributes("-topmost", True)
        win.after(150, lambda: win.attributes("-topmost", False))
        win.focus_force()
    except tk.TclError:
        pass


class Starfield:
    """200-star parallax background; updates every 3 frames."""

    def __init__(self, canvas, w, h, count=200):
        self.canvas = canvas
        self.w, self.h = w, h
        self.stars = []
        speeds = (0.2, 0.5, 1.0)
        for _ in range(count):
            layer = random.randint(0, 2)
            self.stars.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "size": random.choice((1, 1, 2, 2, 3)),
                "speed": speeds[layer] * random.uniform(0.85, 1.15),
                "phase": random.uniform(0, math.pi * 2),
                "ids": [],
            })
        self.tick = 0

    def update(self):
        self.tick += 1
        if self.tick % 3 != 0:
            return
        for s in self.stars:
            for sid in s["ids"]:
                safe_canvas(self.canvas, self.canvas.delete, sid)
            s["ids"].clear()
            s["y"] += s["speed"]
            if s["y"] > self.h:
                s["y"] = 0
                s["x"] = random.uniform(0, self.w)
            t = self.tick * 0.06 + s["phase"]
            bright = int((0.45 + 0.55 * (0.5 + 0.5 * math.sin(t))) * 255)
            color = f"#{bright:02x}{bright:02x}{min(255, bright + 20):02x}"
            x, y, sz = int(s["x"]), int(s["y"]), s["size"]
            oid = safe_canvas(
                self.canvas, self.canvas.create_oval,
                x, y, x + sz, y + sz, fill=color, outline="", tags="bg_star",
            )
            if oid:
                s["ids"].append(oid)
        safe_canvas(self.canvas, self.canvas.tag_lower, "bg_star")


class CanvasButton:
    """Custom rounded HUD button on a canvas."""

    def __init__(self, canvas, x, y, text, command, width=260, height=46):
        self.canvas = canvas
        self.x, self.y = x, y
        self.text = text
        self.command = command
        self.w, self.h = width, height
        self.hover = self.pressed = False
        self.ids = []
        self._draw()
        self._bind_tags()

    def _draw(self):
        for i in self.ids:
            safe_canvas(self.canvas, self.canvas.delete, i)
        self.ids.clear()
        fill = COLORS["panel_active"] if self.pressed else (
            COLORS["panel_hi"] if self.hover else COLORS["panel"]
        )
        border = COLORS["text"] if self.pressed else (
            COLORS["cyan"] if self.hover else COLORS["blue"]
        )
        sc = 0.97 if self.pressed else 1.0
        hw, hh = self.w * sc / 2, self.h * sc / 2
        x1, y1 = self.x - hw, self.y - hh
        x2, y2 = self.x + hw, self.y + hh
        tag = ("ui_btn",)
        body = safe_canvas(
            self.canvas, self.canvas.create_rectangle,
            x1, y1, x2, y2, fill=fill, outline=border, width=2, tags=tag,
        )
        label = safe_canvas(
            self.canvas, self.canvas.create_text,
            self.x, self.y, text=self.text, fill=COLORS["cyan"],
            font=("Arial", 12, "bold"), tags=tag,
        )
        for item in (body, label):
            if item:
                self.ids.append(item)

    def _bind_tags(self):
        for item in self.ids:
            for ev, fn in (
                ("<Enter>", lambda e: self._set_hover(True)),
                ("<Leave>", lambda e: self._set_hover(False)),
                ("<ButtonPress-1>", lambda e: self._press(True)),
                ("<ButtonRelease-1>", lambda e: self._release()),
            ):
                self.canvas.tag_bind(item, ev, fn)

    def _set_hover(self, state):
        self.hover = state
        if not state:
            self.pressed = False
        self._draw()
        self._bind_tags()

    def _press(self, state):
        self.pressed = state
        self._draw()
        self._bind_tags()

    def _release(self):
        ok = self.pressed and self.hover
        self.pressed = False
        self._draw()
        self._bind_tags()
        if ok and self.command:
            self.command()


class LauncherApp:
    """Root application — single Tk instance, navigation via Toplevel + callbacks."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("STARSHIP GALACTIC FRONTIER")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(APP_CONFIG["min_w"], APP_CONFIG["min_h"])
        self.root.geometry(f"{APP_CONFIG['default_w']}x{APP_CONFIG['default_h']}")
        self.username = None
        self.session = {}
        self._menu_after = None
        self._galaxy_window = None
        self._active_child = None

        self.canvas = tk.Canvas(
            self.root,
            width=APP_CONFIG["default_w"],
            height=APP_CONFIG["default_h"],
            bg=COLORS["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.starfield = Starfield(
            self.canvas, APP_CONFIG["default_w"], APP_CONFIG["default_h"], 200,
        )
        self._build_menu()
        self._animate_menu()

    def _build_menu(self):
        cx = APP_CONFIG["default_w"] // 2
        cy = APP_CONFIG["default_h"] // 2
        safe_canvas(
            self.canvas, self.canvas.create_text,
            cx, cy - 120, text="STARSHIP GALACTIC FRONTIER",
            fill=COLORS["cyan"], font=("Arial", 26, "bold"), tags=("ui_btn",),
        )
        safe_canvas(
            self.canvas, self.canvas.create_text,
            cx, cy - 70, text="COMMANDER TERMINAL v2.4.1",
            fill=COLORS["muted"], font=("Arial", 13), tags=("ui_btn",),
        )
        CanvasButton(self.canvas, cx, cy + 20, "LAUNCH MISSION", self.open_login)
        CanvasButton(self.canvas, cx, cy + 78, "CREATE ACCOUNT", self.open_signup)
        CanvasButton(self.canvas, cx, cy + 136, "EXIT", self.root.quit)
        safe_canvas(self.canvas, self.canvas.tag_raise, "ui_btn")

    def _animate_menu(self):
        if not self.canvas.winfo_exists():
            return
        try:
            if not self.canvas.winfo_ismapped():
                return
        except tk.TclError:
            return
        self.starfield.update()
        safe_canvas(self.canvas, self.canvas.tag_raise, "ui_btn")
        self._menu_after = self.canvas.after(33, self._animate_menu)

    def _stop_menu_animation(self):
        if self._menu_after:
            try:
                self.root.after_cancel(self._menu_after)
            except tk.TclError:
                pass
            self._menu_after = None

    def _hide_launcher_menu(self):
        """Hide menu without destroying root."""
        self._stop_menu_animation()
        try:
            self.canvas.pack_forget()
        except tk.TclError:
            pass

    def _show_launcher_menu(self):
        try:
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self._animate_menu()
        except tk.TclError:
            pass

    def open_login(self):
        from login import LoginWindow
        LoginWindow(self.root, on_success=self.after_login)

    def open_signup(self):
        from signup import SignupWindow
        SignupWindow(self.root, on_success=self.open_login_after_signup)

    def open_login_after_signup(self, username=""):
        """Signup success → open login with optional prefill."""
        from login import LoginWindow
        LoginWindow(self.root, on_success=self.after_login, prefill=username)

    def after_login(self, username):
        """Login success → hide launcher → ship select."""
        self.username = username
        self._hide_launcher_menu()
        self.root.withdraw()
        defer(self.root, self._open_ship_select, username)

    def _open_ship_select(self, username):
        from ship_select import ShipSelectWindow
        self._active_child = ShipSelectWindow(
            self.root, username, on_success=self.open_map, app=self,
        )

    def open_map(self, username):
        """Ship confirmed → galaxy map."""
        defer(self.root, self._open_galaxy, username)

    def _open_galaxy(self, username):
        from galaxy_map import GalaxyMapWindow
        if self._galaxy_window:
            try:
                if self._galaxy_window.window.winfo_exists():
                    self._galaxy_window.window.destroy()
            except tk.TclError:
                pass
        self._galaxy_window = GalaxyMapWindow(self.root, username, app=self)
        self._active_child = self._galaxy_window

    def show_pause(self):
        if self._galaxy_window and hasattr(self._galaxy_window, "canvas"):
            from game import PauseOverlay
            PauseOverlay(self._galaxy_window)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    LauncherApp().run()
