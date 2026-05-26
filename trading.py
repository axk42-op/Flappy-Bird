"""
trading.py — Commodity market with dynamic prices and cargo limits.
"""

import random
import tkinter as tk

from databaselogic import get_user_data, save_user_data, update_faction_rep

COMMODITY_LABELS = {
    "ore": "Ore", "fuel_cells": "Fuel Cells", "food": "Food", "medicine": "Medicine",
    "weapons": "Weapons", "luxury": "Luxury Goods", "tech_parts": "Tech Parts",
    "contraband": "Contraband", "artifacts": "Alien Artifacts", "spice": "Spice",
    "data_chips": "Data Chips", "nanites": "Nanites",
}

WEIGHT = {"ore": 2, "artifacts": 3}


class TradingWindow:
    def __init__(self, parent, username, session, system, on_close=None):
        self.parent = parent
        self.username = username
        self.session = session
        self.system = system
        self.on_close = on_close

        from launcher import APP_CONFIG, COLORS, safe_canvas, defer, raise_toplevel
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._safe = safe_canvas
        self._defer = defer

        self.window = tk.Toplevel(parent)
        self.window.title(f"Market — {system['name']}")
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
        self.selected_commodity = "ore"
        self.qty = 1
        self.prices = dict(system["prices"])
        self._vary_prices()
        self._record_history()
        self.canvas.bind("<Button-1>", self._click)
        self.bind_keys()
        self._draw()
        raise_toplevel(self.window)

    def _vary_prices(self):
        rng = random.Random(self.system["id"] + self.session.get("day", 1))
        for k in self.prices:
            self.prices[k] = int(self.prices[k] * rng.uniform(0.85, 1.15))

    def _record_history(self):
        hist = self.session.setdefault("price_history", {})
        sid = str(self.system["id"])
        hist.setdefault(sid, []).append(dict(self.prices))
        hist[sid] = hist[sid][-5:]

    def bind_keys(self):
        self.canvas.bind("<KeyPress>", lambda e: self._key(e))
        self.canvas.focus_set()

    def _key(self, event):
        if event.keysym == "Escape":
            self._close()
        elif event.keysym == "Up":
            self.qty = min(20, self.qty + 1)
            self._draw()
        elif event.keysym == "Down":
            self.qty = max(1, self.qty - 1)
            self._draw()

    def _cargo_weight(self):
        total = 0
        for k, v in self.session.get("cargo", {}).items():
            total += v * WEIGHT.get(k, 1)
        return total

    def _draw(self):
        COLORS = self._colors
        self._safe(self.canvas, self.canvas.delete, "all")
        self._safe(self.canvas, self.canvas.create_text,
                    self._cfg["default_w"] // 2, 40,
                    text=f"MARKET — {self.system['name']}", fill=COLORS["cyan"],
                    font=("Arial", 20, "bold"))
        self._safe(self.canvas, self.canvas.create_text,
                    40, 70, text=f"Credits: {self.session.get('credits', 0)}",
                    fill=COLORS["text"], font=("Courier New", 12), anchor="w")
        self._safe(self.canvas, self.canvas.create_text,
                    40, 92, text=f"Cargo: {self._cargo_weight()}/{self.session.get('cargo_capacity', 20)}",
                    fill=COLORS["text"], font=("Courier New", 12), anchor="w")

        y0 = 130
        keys = list(COMMODITY_LABELS.keys())
        for i, key in enumerate(keys):
            y = y0 + i * 36
            col = COLORS["cyan"] if key == self.selected_commodity else COLORS["text"]
            self._safe(self.canvas, self.canvas.create_text,
                        60, y, text=COMMODITY_LABELS[key], fill=col,
                        font=("Courier New", 11), anchor="w", tags=("row", key))
            self._safe(self.canvas, self.canvas.create_text,
                        280, y, text=f"Buy {self.prices[key]}", fill=COLORS["success"],
                        font=("Courier New", 10), anchor="w", tags=("row", key))
            have = self.session.get("cargo", {}).get(key, 0)
            sell_p = int(self.prices[key] * 0.85)
            self._safe(self.canvas, self.canvas.create_text,
                        400, y, text=f"Sell {sell_p} (x{have})", fill=COLORS["warn"],
                        font=("Courier New", 10), anchor="w", tags=("row", key))

        self._draw_sparkline()
        self._safe(self.canvas, self.canvas.create_text,
                    self._cfg["default_w"] // 2, self._cfg["default_h"] - 140,
                    text=f"Quantity: {self.qty}", fill=COLORS["cyan"], font=("Courier New", 12))

        for label, _cmd, xo in (("BUY", self._buy, -120), ("SELL", self._sell, 0), ("BACK", self._close, 120)):
            x = self._cfg["default_w"] // 2 + xo
            y = self._cfg["default_h"] - 80
            self._safe(self.canvas, self.canvas.create_rectangle,
                        x - 50, y - 16, x + 50, y + 16,
                        fill=COLORS["panel"], outline=COLORS["cyan"], tags=("act", label))
            self._safe(self.canvas, self.canvas.create_text,
                        x, y, text=label, fill=COLORS["cyan"], tags=("act", label))

        self._contraband_check()

    def _draw_sparkline(self):
        COLORS = self._colors
        hist = self.session.get("price_history", {}).get(str(self.system["id"]), [])
        if len(hist) < 2:
            return
        key = self.selected_commodity
        vals = [h.get(key, 0) for h in hist]
        if not vals or max(vals) == 0:
            return
        x0, y0, w, h = 900, 130, 300, 80
        self._safe(self.canvas, self.canvas.create_rectangle,
                    x0, y0, x0 + w, y0 + h, outline=COLORS["blue"], fill=COLORS["panel"])
        mx = max(vals)
        pts = []
        for i, v in enumerate(vals):
            px = x0 + 20 + i * (w - 40) / max(1, len(vals) - 1)
            py = y0 + h - 15 - (v / mx) * (h - 30)
            pts.extend([px, py])
        if len(pts) >= 4:
            self._safe(self.canvas, self.canvas.create_line,
                        *pts, fill=COLORS["cyan"], width=2)

    def _contraband_check(self):
        COLORS = self._colors
        if self.selected_commodity != "contraband":
            return
        if self.system["faction"] in ("empire", "foundation"):
            self._safe(self.canvas, self.canvas.create_text,
                        self._cfg["default_w"] // 2, self._cfg["default_h"] - 180,
                        text="WARNING: Contraband illegal here — inspection risk",
                        fill=COLORS["warn"], font=("Arial", 11))

    def _click(self, event):
        y0 = 130
        keys = list(COMMODITY_LABELS.keys())
        for i, key in enumerate(keys):
            y = y0 + i * 36
            if 50 < event.x < 500 and y - 12 < event.y < y + 12:
                self.selected_commodity = key
                self._draw()
                return
        y = self._cfg["default_h"] - 80
        for label, xo in (("BUY", -120), ("SELL", 0), ("BACK", 120)):
            x = self._cfg["default_w"] // 2 + xo
            if x - 50 < event.x < x + 50 and y - 16 < event.y < y + 16:
                if label == "BUY":
                    self._buy()
                elif label == "SELL":
                    self._sell()
                else:
                    self._close()

    def _buy(self):
        key = self.selected_commodity
        cost = self.prices[key] * self.qty
        w = WEIGHT.get(key, 1) * self.qty
        if self.session.get("credits", 0) < cost:
            return
        if self._cargo_weight() + w > self.session.get("cargo_capacity", 20):
            return
        if key == "contraband" and self.system["faction"] in ("empire", "foundation"):
            if random.random() < 0.35:
                update_faction_rep(self.username, self.system["faction"], -30)
                self.session.setdefault("cargo", {}).pop(key, None)
                self._persist()
                self._draw()
                return
        self.session["credits"] -= cost
        self.session.setdefault("cargo", {})[key] = self.session["cargo"].get(key, 0) + self.qty
        update_faction_rep(self.username, self.system["faction"], 1)
        self._persist()
        self._draw()

    def _sell(self):
        key = self.selected_commodity
        have = self.session.get("cargo", {}).get(key, 0)
        if have < self.qty:
            return
        gain = int(self.prices[key] * 0.85) * self.qty
        self.session["credits"] += gain
        self.session["cargo"][key] = have - self.qty
        if self.session["cargo"][key] <= 0:
            del self.session["cargo"][key]
        update_faction_rep(self.username, self.system["faction"], 1)
        self._persist()
        self._draw()

    def _persist(self):
        data = get_user_data(self.username)
        data["session"] = self.session
        data["credits"] = self.session["credits"]
        save_user_data(self.username, data)

    def _close(self):
        cb = self.on_close
        host = self.parent
        self.window.destroy()
        if cb:
            self._defer(host, cb)
