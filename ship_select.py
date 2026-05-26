"""
ship_select.py — Starship selection (Toplevel + on_success callback).
"""

import tkinter as tk

from databaselogic import get_user_data, set_selected_ship

SHIP_POLYGONS = {
    "falcon": [(0, -18), (16, 14), (0, 8), (-16, 14)],
    "interceptor": [(0, -22), (10, 0), (0, 18), (22, 10), (0, 4), (-10, 0)],
    "dreadnought": [(0, -16), (24, -4), (20, 18), (-20, 18), (-24, -4)],
    "merchant": [(0, -14), (26, 6), (18, 20), (-18, 20), (-26, 6)],
    "phantom": [(0, -20), (8, -6), (18, 12), (0, 16), (-18, 12), (-8, -6)],
}

SHIPS = {
    "falcon": {
        "name": "Falcon", "speed": 6, "hull": 6, "fire": 6, "cargo": 5,
        "special": "Balanced — ideal for new commanders",
    },
    "interceptor": {
        "name": "Interceptor", "speed": 9, "hull": 4, "fire": 7, "cargo": 3,
        "special": "Afterburner dash (Shift)",
    },
    "dreadnought": {
        "name": "Dreadnought", "speed": 3, "hull": 10, "fire": 9, "cargo": 4,
        "special": "Auto-repair 1 HP / 5s",
    },
    "merchant": {
        "name": "Merchant", "speed": 4, "hull": 5, "fire": 3, "cargo": 10,
        "special": "Trade prices -10%",
    },
    "phantom": {
        "name": "Phantom", "speed": 7, "hull": 5, "fire": 6, "cargo": 5,
        "special": "Stealth cloak 3s (E)",
    },
}


class ShipSelectWindow:
    """Ship picker Toplevel; on_success(username) deferred after confirm."""

    def __init__(self, parent, username, on_success=None, app=None):
        self.parent = parent
        self.username = username
        self.on_success = on_success
        self.app = app
        self._after_id = None

        from launcher import APP_CONFIG, COLORS, Starfield, safe_canvas, defer, raise_toplevel
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._safe = safe_canvas
        self._defer = defer

        self.window = tk.Toplevel(parent)
        self.window.title("STARSHIP GALACTIC FRONTIER — Ship Select")
        self.window.configure(bg=COLORS["bg"])
        self.window.geometry(f"{APP_CONFIG['default_w']}x{APP_CONFIG['default_h']}")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self.canvas = tk.Canvas(
            self.window,
            width=APP_CONFIG["default_w"],
            height=APP_CONFIG["default_h"],
            bg=COLORS["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.starfield = Starfield(
            self.canvas, APP_CONFIG["default_w"], APP_CONFIG["default_h"], 100,
        )
        data = get_user_data(username)
        self.hover = data.get("selected_ship", "falcon")
        self._build()
        self.canvas.bind("<Button-1>", self._click)
        self._tick()
        raise_toplevel(self.window)

    def _build(self):
        COLORS = self._colors
        cx = self._cfg["default_w"] // 2
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, 50, text="SELECT STARSHIP", fill=COLORS["cyan"],
            font=("Arial", 22, "bold"), tags=("ui",),
        )
        slots = [cx - 400, cx - 200, cx, cx + 200, cx + 400]
        keys = list(SHIPS.keys())
        for i, sid in enumerate(keys):
            self._draw_ship_card(slots[i], 280, sid, sid == self.hover)
        self._safe(
            self.canvas, self.canvas.create_rectangle,
            cx - 110, self._cfg["default_h"] - 100,
            cx + 110, self._cfg["default_h"] - 60,
            fill=COLORS["panel"], outline=COLORS["cyan"], tags=("ui",),
        )
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, self._cfg["default_h"] - 80,
            text="CONFIRM DEPLOYMENT", fill=COLORS["cyan"],
            font=("Courier New", 12), tags=("ui",),
        )

    def _draw_ship_card(self, cx, cy, sid, selected):
        COLORS = self._colors
        cfg = SHIPS[sid]
        col = COLORS["cyan"] if selected else COLORS["blue"]
        self._safe(
            self.canvas, self.canvas.create_rectangle,
            cx - 90, cy - 120, cx + 90, cy + 120,
            fill=COLORS["panel"], outline=col, width=2, tags=("ui",),
        )
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, cy - 100, text=cfg["name"].upper(), fill=col,
            font=("Arial", 12, "bold"), tags=("ui",),
        )
        pts = SHIP_POLYGONS[sid]
        scaled = [(cx + px * 2, cy - 30 + py * 2) for px, py in pts]
        flat = [c for p in scaled for c in p]
        self._safe(
            self.canvas, self.canvas.create_polygon,
            *flat, fill=COLORS["panel_hi"], outline=col, width=2, tags=("ui",),
        )
        labels = ("Speed", "Hull", "Firepower", "Cargo")
        stats = (cfg["speed"], cfg["hull"], cfg["fire"], cfg["cargo"])
        for j, (lab, val) in enumerate(zip(labels, stats)):
            by = cy + 20 + j * 22
            self._safe(
                self.canvas, self.canvas.create_text,
                cx - 70, by, text=lab, fill=COLORS["muted"],
                font=("Courier New", 9), anchor="w", tags=("ui",),
            )
            self._safe(
                self.canvas, self.canvas.create_rectangle,
                cx - 10, by - 6, cx + 70, by + 6,
                outline=COLORS["blue"], fill=COLORS["bg"], tags=("ui",),
            )
            self._safe(
                self.canvas, self.canvas.create_rectangle,
                cx - 10, by - 6, cx - 10 + val * 6, by + 6,
                fill=col, outline="", tags=("ui",),
            )
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, cy + 105, text=cfg["special"][:28], fill=COLORS["text"],
            font=("Arial", 8), tags=("ui",),
        )

    def _click(self, event):
        cx = self._cfg["default_w"] // 2
        slots = [cx - 400, cx - 200, cx, cx + 200, cx + 400]
        keys = list(SHIPS.keys())
        for i, sx in enumerate(slots):
            if abs(event.x - sx) < 90 and 160 < event.y < 400:
                self.hover = keys[i]
                self.canvas.delete("ui")
                self._build()
                return
        if (cx - 110 < event.x < cx + 110 and
                self._cfg["default_h"] - 100 < event.y < self._cfg["default_h"] - 60):
            self._confirm()

    def _confirm(self):
        set_selected_ship(self.username, self.hover)
        self._finish_success(self.username)

    def _finish_success(self, username):
        self._cancel_after()
        cb = self.on_success
        parent = self.parent
        self.window.destroy()
        if cb:
            self._defer(parent, cb, username)

    def _cancel_after(self):
        if self._after_id:
            try:
                self.window.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _tick(self):
        if not self.window.winfo_exists():
            return
        self.starfield.update()
        self._after_id = self.window.after(50, self._tick)

    def _on_close(self):
        self._cancel_after()
        self.window.destroy()
        try:
            self.parent.deiconify()
            if self.app:
                self.app._show_launcher_menu()
        except tk.TclError:
            pass
