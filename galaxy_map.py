"""
galaxy_map.py — Procedural galaxy map with travel, trade hooks, and faction colors.
"""

import math
import tkinter as tk

from databaselogic import (
    get_galaxy,
    get_user_data,
    mark_system_discovered,
    save_user_data,
    update_faction_rep,
)

FACTION_COLORS = {
    "empire": "#ff4444",
    "foundation": "#00f5ff",
    "pirates": "#ffaa00",
    "guild": "#00ff88",
    "ai": "#aa44ff",
}

VIEW_W, VIEW_H = 1000, 700


class GalaxyMapWindow:
    """Main galaxy view as Toplevel (stays open for the session)."""

    def __init__(self, parent, username, on_success=None, app=None):
        self.parent = parent
        self.username = username
        self.on_success = on_success
        self.app = app
        self._loop_after = None

        from launcher import APP_CONFIG, COLORS, safe_canvas, raise_toplevel
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._safe = safe_canvas

        self.window = tk.Toplevel(parent)
        self.window.title(f"Galaxy Map — {username}")
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

        self.galaxy = get_galaxy(self.username)
        self.systems = self.galaxy["systems"]
        self.lanes = self.galaxy["lanes"]
        data = get_user_data(self.username)
        self.session = data["session"]
        self.session["credits"] = data.get("credits", 500)
        self.discovered = set(data.get("discovered_systems", [0]))
        self.faction_rep = data.get("faction_rep", {})
        self.selected = self.session.get("current_system", 0)
        self.pan_x = self.pan_y = 0.0
        self.info_panel = ""
        self._drag = None
        self.bind_keys()
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._draw()
        self._loop()
        raise_toplevel(self.window)

    def bind_keys(self):
        self.canvas.bind("<KeyPress>", self._key)
        self.canvas.focus_set()

    def _key(self, event):
        step = 30
        k = event.keysym
        if k == "Left":
            self.pan_x += step
        elif k == "Right":
            self.pan_x -= step
        elif k == "Up":
            self.pan_y += step
        elif k == "Down":
            self.pan_y -= step
        elif k.lower() == "m":
            self._draw()
        elif k.lower() == "t" and self.selected is not None:
            self._dock_trade()
        elif k.lower() == "u":
            self._upgrades()
        elif k == "Escape" and self.app:
            self.app.show_pause()
        self._draw()

    def _world_to_screen(self, wx, wy):
        ox = self._cfg["default_w"] // 2 - VIEW_W // 2 + self.pan_x
        oy = 80 + self.pan_y
        return wx + ox, wy + oy

    def _draw(self):
        COLORS = self._colors
        self._safe(self.canvas, self.canvas.delete, "all")
        ox = self._cfg["default_w"] // 2 - VIEW_W // 2 + self.pan_x
        oy = 80 + self.pan_y
        self._safe(self.canvas, self.canvas.create_rectangle,
                    ox, oy, ox + VIEW_W, oy + VIEW_H,
                    fill="#050814", outline=COLORS["cyan"], tags=("map",))

        for i, j in self.lanes:
            a, b = self.systems[i], self.systems[j]
            x1, y1 = self._world_to_screen(a["x"], a["y"])
            x2, y2 = self._world_to_screen(b["x"], b["y"])
            self._safe(self.canvas, self.canvas.create_line,
                        x1, y1, x2, y2, fill=COLORS["blue"], width=1, tags=("map",))

        for sys in self.systems:
            sx, sy = self._world_to_screen(sys["x"], sys["y"])
            col = FACTION_COLORS.get(sys["faction"], COLORS["muted"])
            r = 10 if sys["id"] in self.discovered else 6
            if sys["id"] not in self.discovered:
                col = COLORS["muted"]
            self._safe(self.canvas, self.canvas.create_oval,
                        sx - r, sy - r, sx + r, sy + r,
                        fill=col, outline=COLORS["text"], tags=("map", "sys", f"s{sys['id']}"))
            if sys["id"] in self.discovered:
                self._safe(self.canvas, self.canvas.create_text,
                            sx, sy - 16, text=sys["name"][:12], fill=COLORS["text"],
                            font=("Arial", 8), tags=("map",))

        cur = self.systems[self.session.get("current_system", 0)]
        px, py = self._world_to_screen(cur["x"], cur["y"])
        pts = [(px, py - 10), (px + 8, py + 8), (px - 8, py + 8)]
        flat = [c for p in pts for c in p]
        self._safe(self.canvas, self.canvas.create_polygon,
                    *flat, fill=COLORS["cyan"], outline=COLORS["text"], tags=("map",))

        self._draw_hud_strip()
        self._draw_info_panel()
        self._draw_buttons()

    def _draw_hud_strip(self):
        COLORS = self._colors
        y = 20
        cur = self.systems[self.session["current_system"]]
        txt = (
            f"Credits: {self.session.get('credits', 0)}  |  Fuel: {self.session.get('fuel', 0)}  |  "
            f"Hull: {self.session.get('hull', 0)}/{self.session.get('max_hull', 100)}  |  "
            f"Cargo: {self._cargo_used()}/{self.session.get('cargo_capacity', 20)}  |  "
            f"System: {cur['name']}"
        )
        self._safe(self.canvas, self.canvas.create_text,
                    20, y, text=txt, fill=COLORS["cyan"], font=("Courier New", 11),
                    anchor="w", tags=("hud",))
        rep = self.faction_rep.get(cur["faction"], 0)
        self._safe(self.canvas, self.canvas.create_text,
                    self._cfg["default_w"] - 20, y,
                    text=f"Faction ({cur['faction']}): {rep}",
                    fill=COLORS["success"] if rep > 0 else COLORS["danger"],
                    font=("Courier New", 11), anchor="e", tags=("hud",))

    def _cargo_used(self):
        cargo = self.session.get("cargo", {})
        total = 0
        weights = {"ore": 2, "artifacts": 3}
        for k, v in cargo.items():
            total += v * weights.get(k, 1)
        return total

    def _draw_info_panel(self):
        if self.selected is None:
            return
        COLORS = self._colors
        sys = self.systems[self.selected]
        px = self._cfg["default_w"] - 280
        py = 100
        self._safe(self.canvas, self.canvas.create_rectangle,
                    px, py, px + 260, py + 200,
                    fill=COLORS["panel"], outline=COLORS["cyan"], tags=("hud",))
        lines = [
            sys["name"],
            f"Faction: {sys['faction']}",
            f"Economy: {sys['economy']}",
            f"Threat: {sys['threat']}/5",
            f"Star: {sys['star_type']}",
            f"Planets: {sys['planets']}",
        ]
        if self.selected in self.discovered or self.selected == self.session["current_system"]:
            lines.append(f"Rep: {self.faction_rep.get(sys['faction'], 0)}")
        for i, line in enumerate(lines):
            self._safe(self.canvas, self.canvas.create_text,
                        px + 12, py + 18 + i * 22, text=line, fill=COLORS["text"],
                        font=("Arial", 11), anchor="w", tags=("hud",))

    def _draw_buttons(self):
        COLORS = self._colors
        bx = self._cfg["default_w"] // 2 - 200
        by = self._cfg["default_h"] - 50
        for i, label in enumerate(("TRAVEL", "TRADE", "DOCK", "SCAN")):
            x = bx + i * 110
            self._safe(self.canvas, self.canvas.create_rectangle,
                        x - 48, by - 18, x + 48, by + 18,
                        fill=COLORS["panel"], outline=COLORS["cyan"], tags=("btn", label))
            self._safe(self.canvas, self.canvas.create_text,
                        x, by, text=label, fill=COLORS["cyan"],
                        font=("Courier New", 10), tags=("btn", label))

    def _on_press(self, event):
        if event.y > self._cfg["default_h"] - 70:
            self._handle_btn(event.x, event.y)
            return
        if event.y < self._cfg["default_h"] - 80:
            self._drag = (event.x, event.y)
        for sys in self.systems:
            sx, sy = self._world_to_screen(sys["x"], sys["y"])
            if math.hypot(event.x - sx, event.y - sy) < 14:
                self.selected = sys["id"]
                self._draw()
                return

    def _handle_btn(self, mx, my):
        bx = self._cfg["default_w"] // 2 - 200
        by = self._cfg["default_h"] - 50
        labels = ("TRAVEL", "TRADE", "DOCK", "SCAN")
        for i, label in enumerate(labels):
            x = bx + i * 110
            if x - 48 < mx < x + 48 and by - 18 < my < by + 18:
                getattr(self, f"_action_{label.lower()}")()
                return

    def _action_travel(self):
        if self.selected is None:
            return
        cur_id = self.session["current_system"]
        if self.selected == cur_id:
            return
        a = self.systems[cur_id]
        b = self.systems[self.selected]
        dist = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
        fuel_cost = max(5, int(dist / 40))
        if self.session.get("fuel", 0) < fuel_cost:
            self.info_panel = "Insufficient fuel."
            self._draw()
            return
        self.session["fuel"] -= fuel_cost
        self.session["current_system"] = self.selected
        mark_system_discovered(self.username, self.selected)
        self.discovered.add(self.selected)
        sys = self.systems[self.selected]
        rep = self.faction_rep.get(sys["faction"], 0)
        if sys["threat"] >= 4 and rep < -20:
            self._launch_combat()
        else:
            update_faction_rep(self.username, sys["faction"], 1)
        self._persist()
        self._draw()

    def _action_trade(self):
        self._dock_trade()

    def _action_dock(self):
        self._dock_trade()

    def _action_scan(self):
        mark_system_discovered(self.username, self.selected)
        self.discovered.add(self.selected)
        self._persist()
        self._draw()

    def _dock_trade(self):
        import trading
        trading.TradingWindow(
            self.window, self.username, self.session,
            self.systems[self.session["current_system"]],
            on_close=self._refresh,
        )

    def _upgrades(self):
        import upgrades
        upgrades.UpgradesWindow(self.window, self.username, on_close=self._refresh)

    def _launch_combat(self):
        import combat
        combat.CombatWindow(
            self.window, self.username, self.session,
            on_end=self._combat_return,
        )

    def _refresh(self):
        data = get_user_data(self.username)
        self.session = data["session"]
        self.session["credits"] = data.get("credits", self.session.get("credits", 0))
        self.faction_rep = data.get("faction_rep", self.faction_rep)
        self._draw()

    def _combat_return(self, result):
        if result.get("victory"):
            self.session["credits"] = self.session.get("credits", 0) + result.get("credits", 0)
            loot = result.get("loot", {})
            for k, v in loot.items():
                self.session.setdefault("cargo", {})[k] = self.session["cargo"].get(k, 0) + v
            update_faction_rep(self.username, self.systems[self.session["current_system"]]["faction"], 5)
        else:
            self.session["hull"] = max(1, self.session.get("hull", 50) - 20)
        self._persist()
        self._draw()

    def _persist(self):
        data = get_user_data(self.username)
        data["session"] = self.session
        data["credits"] = self.session.get("credits", data.get("credits", 0))
        save_user_data(self.username, data)

    def _on_drag(self, event):
        if self._drag:
            dx = event.x - self._drag[0]
            dy = event.y - self._drag[1]
            self.pan_x += dx
            self.pan_y += dy
            self._drag = (event.x, event.y)
            self._draw()

    def _on_release(self, event):
        self._drag = None

    def _loop(self):
        if not self.window.winfo_exists():
            return
        self._loop_after = self.window.after(100, self._loop)

    def _on_close(self):
        if self._loop_after:
            try:
                self.window.after_cancel(self._loop_after)
            except tk.TclError:
                pass
        self.window.destroy()
        try:
            self.parent.deiconify()
            if self.app:
                self.app._show_launcher_menu()
        except tk.TclError:
            pass


def open_galaxy(parent, username, app=None):
    return GalaxyMapWindow(parent, username, app=app)
