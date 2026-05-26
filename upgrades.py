"""
upgrades.py — Ship upgrade hangar with 8 modular slots (tiers I–V).
"""

import tkinter as tk

from databaselogic import apply_upgrade, get_user_data

SLOTS = (
    ("engine", "Engine", 0, -120),
    ("hull", "Hull Plating", -140, -40),
    ("primary", "Primary Weapon", 140, -40),
    ("secondary", "Secondary Weapon", 160, 40),
    ("shield", "Shield Generator", -160, 40),
    ("scanner", "Scanner Array", -100, 120),
    ("cargo", "Cargo Expander", 100, 120),
    ("stealth", "Stealth Module", 0, 140),
)

TIER_COSTS = [500, 1200, 2800, 6000, 12000]
ROMAN = ("0", "I", "II", "III", "IV", "V")


class UpgradesWindow:
    def __init__(self, parent, username, on_close=None):
        self.parent = parent
        self.username = username
        self.on_close = on_close

        from launcher import APP_CONFIG, COLORS, safe_canvas, defer, raise_toplevel
        from ship_select import SHIP_POLYGONS
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._safe = safe_canvas
        self._defer = defer
        self._polygons = SHIP_POLYGONS

        self.window = tk.Toplevel(parent)
        self.window.title("Ship Upgrades")
        self.window.configure(bg=COLORS["bg"])
        self.window.geometry(f"{APP_CONFIG['default_w']}x{APP_CONFIG['default_h']}")
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self._close)

        self.canvas = tk.Canvas(
            self.window,
            width=APP_CONFIG["default_w"],
            height=APP_CONFIG["default_h"],
            bg=COLORS["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.data = get_user_data(self.username)
        self.upgrades = self.data.get("ship_upgrades", {})
        self.ship = self.data.get("selected_ship", "falcon")
        self.selected_slot = "engine"
        self.canvas.bind("<Button-1>", self._click)
        self._draw()
        raise_toplevel(self.window)

    def _draw(self):
        COLORS = self._colors
        self._safe(self.canvas, self.canvas.delete, "all")
        cx, cy = self._cfg["default_w"] // 2, self._cfg["default_h"] // 2
        self._safe(self.canvas, self.canvas.create_text,
                    cx, 50, text="SHIP UPGRADES", fill=COLORS["cyan"], font=("Arial", 22, "bold"))
        self._safe(self.canvas, self.canvas.create_text,
                    cx, 78, text=f"Credits: {self.data.get('credits', 0)}",
                    fill=COLORS["text"], font=("Courier New", 12))

        pts = self._polygons.get(self.ship, self._polygons["falcon"])
        scaled = [(cx + px * 3, cy + py * 3) for px, py in pts]
        flat = [c for p in scaled for c in p]
        self._safe(self.canvas, self.canvas.create_polygon,
                    *flat, fill=COLORS["panel"], outline=COLORS["cyan"], width=2)

        for key, label, ox, oy in SLOTS:
            nx, ny = cx + ox, cy + oy
            tier = self.upgrades.get(key, 0)
            col = COLORS["cyan"] if key == self.selected_slot else COLORS["blue"]
            self._safe(self.canvas, self.canvas.create_line,
                        cx, cy, nx, ny, fill=COLORS["blue"], width=1)
            self._safe(self.canvas, self.canvas.create_oval,
                        nx - 22, ny - 22, nx + 22, ny + 22,
                        fill=COLORS["panel_hi"], outline=col, width=2, tags=("slot", key))
            self._safe(self.canvas, self.canvas.create_text,
                        nx, ny - 6, text=label[:10], fill=COLORS["text"],
                        font=("Arial", 8), tags=("slot", key))
            self._safe(self.canvas, self.canvas.create_text,
                        nx, ny + 10, text=ROMAN[tier], fill=col,
                        font=("Courier New", 10, "bold"), tags=("slot", key))

        self._draw_detail(cx, cy + 200)
        self._safe(self.canvas, self.canvas.create_rectangle,
                    cx - 60, self._cfg["default_h"] - 70,
                    cx + 60, self._cfg["default_h"] - 40,
                    fill=COLORS["panel"], outline=COLORS["cyan"], tags=("back",))
        self._safe(self.canvas, self.canvas.create_text,
                    cx, self._cfg["default_h"] - 55, text="BACK",
                    fill=COLORS["cyan"], tags=("back",))

    def _draw_detail(self, cx, cy):
        COLORS = self._colors
        key = self.selected_slot
        tier = self.upgrades.get(key, 0)
        self._safe(self.canvas, self.canvas.create_rectangle,
                    cx - 280, cy - 50, cx + 280, cy + 50,
                    fill=COLORS["panel"], outline=COLORS["cyan"])
        desc = self._slot_desc(key, tier)
        self._safe(self.canvas, self.canvas.create_text,
                    cx, cy - 20, text=desc, fill=COLORS["text"], font=("Arial", 11))
        if tier < 5:
            cost = TIER_COSTS[tier]
            self._safe(self.canvas, self.canvas.create_rectangle,
                        cx - 80, cy + 10, cx + 80, cy + 40,
                        fill=COLORS["panel_hi"], outline=COLORS["success"], tags=("buy",))
            self._safe(self.canvas, self.canvas.create_text,
                        cx, cy + 25, text=f"UPGRADE — {cost} CR", fill=COLORS["success"], tags=("buy",))
        else:
            self._safe(self.canvas, self.canvas.create_text,
                        cx, cy + 25, text="MAX TIER", fill=COLORS["muted"])

    def _slot_desc(self, key, tier):
        texts = {
            "engine": "Speed +0.5 per tier",
            "hull": "Max hull +20 per tier",
            "primary": "Primary damage +15% per tier",
            "secondary": "Missile/EMP unlock tiers",
            "shield": "Shield capacity scaling",
            "scanner": "Reveal intel on galaxy map",
            "cargo": "+5 cargo per tier",
            "stealth": "Cloak duration +1s per tier",
        }
        return f"{texts.get(key, key)} — Tier {ROMAN[tier]}"

    def _click(self, event):
        cx, cy = self._cfg["default_w"] // 2, self._cfg["default_h"] // 2
        for key, label, ox, oy in SLOTS:
            nx, ny = cx + ox, cy + oy
            if math_dist(event.x, event.y, nx, ny) < 24:
                self.selected_slot = key
                self._draw()
                return
        buy_y = self._cfg["default_h"] // 2 + 200
        if cx - 80 < event.x < cx + 80 and buy_y + 10 < event.y < buy_y + 40:
            if apply_upgrade(self.username, self.selected_slot):
                self.data = get_user_data(self.username)
                self.upgrades = self.data.get("ship_upgrades", {})
                self._draw()
        if self._cfg["default_h"] - 70 < event.y < self._cfg["default_h"] - 40:
            self._close()

    def _close(self):
        cb = self.on_close
        host = self.parent
        self.window.destroy()
        if cb:
            self._defer(host, cb)


def math_dist(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
