"""
combat.py — Top-down real-time space combat module.
"""

import math
import random
import tkinter as tk

from launcher import APP_CONFIG, COLORS, safe_canvas

W, H = APP_CONFIG["default_w"], APP_CONFIG["default_h"]


def safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except tk.TclError:
        return None


class Projectile:
    def __init__(self, x, y, vx, vy, damage, owner, ptype="laser", life=2.0):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.damage = damage
        self.owner = owner
        self.ptype = ptype
        self.life = life
        self.alive = True
        self.ids = []

    def bbox(self):
        return (self.x - 3, self.y - 3, self.x + 3, self.y + 3)

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.life -= dt
        if self.life <= 0 or self.x < -20 or self.x > W + 20 or self.y < -20 or self.y > H + 20:
            self.alive = False

    def draw(self, canvas):
        for i in self.ids:
            safe(canvas.delete, i)
        self.ids.clear()
        if not self.alive:
            return
        col = COLORS["cyan"] if self.owner == "player" else COLORS["danger"]
        oid = safe(canvas.create_rectangle, int(self.x - 2), int(self.y - 6),
                   int(self.x + 2), int(self.y + 6), fill=col, outline="")
        if oid:
            self.ids.append(oid)


class Explosion:
    def __init__(self, x, y, radius=30):
        self.x, self.y = float(x), float(y)
        self.radius = 4.0
        self.max_r = float(radius)
        self.frame = 0
        self.alive = True
        self.ids = []

    def update(self, dt):
        self.radius += 90 * dt
        self.frame += 1
        if self.radius > self.max_r or self.frame > 8:
            self.alive = False

    def draw(self, canvas):
        for i in self.ids:
            safe(canvas.delete, i)
        self.ids.clear()
        if not self.alive:
            return
        colors = ("#ff6600", "#ff9900", "#ffcc00")
        c = colors[min(self.frame // 3, 2)]
        r = self.radius
        oid = safe(canvas.create_oval, int(self.x - r), int(self.y - r),
                   int(self.x + r), int(self.y + r), outline=c, width=2)
        if oid:
            self.ids.append(oid)


class Loot:
    def __init__(self, x, y, ltype, value=1):
        self.x, self.y = float(x), float(y)
        self.ltype = ltype
        self.value = value
        self.alive = True
        self.ids = []

    def bbox(self):
        return (self.x - 10, self.y - 10, self.x + 10, self.y + 10)

    def draw(self, canvas):
        for i in self.ids:
            safe(canvas.delete, i)
        self.ids.clear()
        cols = {"credits": COLORS["success"], "fuel": COLORS["blue"],
                "cargo": COLORS["warn"], "part": COLORS["cyan"], "blueprint": "#ff44ff"}
        oid = safe(canvas.create_oval, int(self.x - 6), int(self.y - 6),
                   int(self.x + 6), int(self.y + 6), fill=cols.get(self.ltype, COLORS["text"]), outline="")
        if oid:
            self.ids.append(oid)


class PlayerShip:
    def __init__(self, session, ship_id):
        self.x, self.y = W / 2, H * 0.75
        self.vx = self.vy = 0.0
        self.angle = -math.pi / 2
        self.session = session
        self.ship_id = ship_id
        self.hull = float(session.get("hull", 100))
        self.max_hull = float(session.get("max_hull", 100))
        self.shield = 0.0
        self.max_shield = session.get("shield_max", 0)
        self.energy = 100.0
        self.primary_cd = 0.0
        self.secondary_cd = 0.0
        self.missiles = 8
        self.shield_cd = 0.0
        self.stealth_timer = 0.0
        self.ids = []
        upgrades = session.get("upgrades", {})
        self.dmg_mult = 1.0 + 0.15 * upgrades.get("primary", 0)
        self.speed = 4.0 + 0.5 * upgrades.get("engine", 0)

    def bbox(self):
        return (self.x - 18, self.y - 18, self.x + 18, self.y + 18)

    def update(self, dt, keys, mouse, fire_pri, fire_sec):
        thrust = self.speed
        if "w" in keys or "Up" in keys:
            self.vx += math.cos(self.angle) * thrust * dt
            self.vy += math.sin(self.angle) * thrust * dt
        if "s" in keys or "Down" in keys:
            self.vx -= math.cos(self.angle) * thrust * 0.6 * dt
            self.vy -= math.sin(self.angle) * thrust * 0.6 * dt
        if "a" in keys or "Left" in keys:
            self.angle -= 3.5 * dt
        if "d" in keys or "Right" in keys:
            self.angle += 3.5 * dt
        if mouse:
            self.angle = math.atan2(mouse[1] - self.y, mouse[0] - self.x)
        self.vx *= 0.98
        self.vy *= 0.98
        self.x = max(30, min(W - 30, self.x + self.vx * dt * 60))
        self.y = max(30, min(H - 30, self.y + self.vy * dt * 60))
        self.primary_cd = max(0, self.primary_cd - dt)
        self.secondary_cd = max(0, self.secondary_cd - dt)
        self.shield_cd = max(0, self.shield_cd - dt)
        if self.stealth_timer > 0:
            self.stealth_timer -= dt
        projectiles = []
        if fire_pri and self.primary_cd <= 0:
            self.primary_cd = 0.15
            spd = 14
            projectiles.append(Projectile(
                self.x + math.cos(self.angle) * 20, self.y + math.sin(self.angle) * 20,
                math.cos(self.angle) * spd, math.sin(self.angle) * spd,
                12 * self.dmg_mult, "player", "laser",
            ))
        if fire_sec and self.secondary_cd <= 0 and self.missiles > 0:
            self.secondary_cd = 0.5
            self.missiles -= 1
            projectiles.append(Projectile(
                self.x, self.y, 0, -10, 25, "player", "missile", life=4.0,
            ))
        return projectiles

    def draw(self, canvas):
        for i in self.ids:
            safe(canvas.delete, i)
        self.ids.clear()
        if self.stealth_timer > 0:
            return
        cx, cy = int(self.x), int(self.y)
        pts = []
        for ang in (-0.5, 0, 0.5):
            a = self.angle + ang
            pts.extend([cx + math.cos(a) * 18, cy + math.sin(a) * 18])
        oid = safe(canvas.create_polygon, *pts, fill=COLORS["panel_hi"], outline=COLORS["cyan"], width=2)
        if oid:
            self.ids.append(oid)


class EnemyShip:
    TYPES = ("drone", "frigate", "cruiser", "boss")

    def __init__(self, x, y, etype, wave):
        self.x, self.y = float(x), float(y)
        self.etype = etype
        self.wave = wave
        scale = 1.08 ** (wave - 1)
        stats = {
            "drone": (20, 3.5, 8),
            "frigate": (55, 2.2, 14),
            "cruiser": (120, 1.2, 18),
            "boss": (400, 0.8, 22),
        }
        hp, spd, dmg = stats.get(etype, (20, 2, 8))
        self.max_hp = hp * scale
        self.hp = self.max_hp
        self.speed = spd
        self.damage = dmg
        self.alive = True
        self.shoot_cd = random.uniform(0.5, 1.5)
        self.phase = 0
        self.orbit_dir = random.choice([-1, 1])
        self.ids = []
        self.drones_spawned = False

    def bbox(self):
        r = 22 if self.etype == "boss" else 14
        return (self.x - r, self.y - r, self.x + r, self.y + r)

    def update(self, dt, player):
        if not self.alive:
            return []
        self.phase += dt
        px, py = player.x, player.y
        dx, dy = px - self.x, py - self.y
        dist = math.hypot(dx, dy) or 1
        shots = []
        if self.etype == "drone":
            self.x += (dx / dist) * self.speed * dt * 60
            self.y += (dy / dist) * self.speed * dt * 60
            if dist < 200 and self.shoot_cd <= 0:
                self.shoot_cd = 0.8
                shots.append(Projectile(self.x, self.y, dx / dist * 6, dy / dist * 6, self.damage, "enemy"))
        elif self.etype == "frigate":
            self.x += self.orbit_dir * self.speed * dt * 60
            self.y += (dy / dist) * self.speed * 0.5 * dt * 60
            if 250 < dist < 350 and self.shoot_cd <= 0:
                self.shoot_cd = 0.5
                for off in (-0.2, 0, 0.2):
                    a = math.atan2(dy, dx) + off
                    shots.append(Projectile(self.x, self.y, math.cos(a) * 7, math.sin(a) * 7, self.damage, "enemy"))
        elif self.etype == "cruiser":
            self.angle_orbit = getattr(self, "angle_orbit", 0) + 0.8 * dt * self.orbit_dir
            self.x = px + math.cos(self.angle_orbit) * 280
            self.y = py + math.sin(self.angle_orbit) * 180
            if self.shoot_cd <= 0:
                self.shoot_cd = 3.0
                for i in range(5):
                    a = -0.4 + i * 0.2
                    shots.append(Projectile(self.x, self.y, math.cos(a) * 5, math.sin(a) * 5 + 4, self.damage, "enemy"))
            if self.hp < self.max_hp * 0.5 and not self.drones_spawned:
                self.drones_spawned = True
                shots.extend([])  # signaled via return drones list separately
        elif self.etype == "boss":
            self.boss_phase = int(getattr(self, "boss_phase", 1))
            if self.boss_phase == 1:
                self.x = px + math.cos(self.phase) * 200
                self.y = 120 + math.sin(self.phase * 0.7) * 40
                if self.shoot_cd <= 0:
                    self.shoot_cd = 0.4
                    shots.append(Projectile(self.x, self.y, 0, 8, self.damage, "enemy"))
            elif self.boss_phase == 2:
                self.x += (dx / dist) * 4 * dt * 60
                self.y += (dy / dist) * 4 * dt * 60
                if self.shoot_cd <= 0:
                    self.shoot_cd = 0.25
                    a = math.atan2(dy, dx)
                    shots.append(Projectile(self.x, self.y, math.cos(a) * 12, math.sin(a) * 12, self.damage * 1.5, "enemy"))
            else:
                if self.shoot_cd <= 0:
                    self.shoot_cd = 0.6
                    for _ in range(3):
                        shots.append(Projectile(self.x + random.randint(-40, 40), self.y,
                                              random.uniform(-4, 4), 6, self.damage, "enemy"))
            if self.hp < self.max_hp * 0.66:
                self.boss_phase = 2
            if self.hp < self.max_hp * 0.33:
                self.boss_phase = 3
        return shots

    def draw(self, canvas):
        for i in self.ids:
            safe(canvas.delete, i)
        self.ids.clear()
        r = 24 if self.etype == "boss" else 12
        col = COLORS["danger"] if self.etype != "drone" else COLORS["warn"]
        oid = safe(canvas.create_oval, int(self.x - r), int(self.y - r),
                   int(self.x + r), int(self.y + r), fill=COLORS["panel"], outline=col, width=2)
        if oid:
            self.ids.append(oid)


class HUD:
    @staticmethod
    def draw(canvas, player, wave, enemies_left, boss=None):
        hp_pct = player.hull / max(1, player.max_hull)
        col = COLORS["success"] if hp_pct > 0.5 else (COLORS["warn"] if hp_pct > 0.25 else COLORS["danger"])
        safe(canvas.create_rectangle, 20, 20, 220, 36, fill=COLORS["panel"], outline=COLORS["cyan"])
        safe(canvas.create_rectangle, 20, 20, 20 + int(200 * hp_pct), 36, fill=col, outline="")
        safe(canvas.create_text, 230, 28, text=f"HULL {int(player.hull)}", fill=COLORS["text"],
             font=("Courier New", 10), anchor="w")
        if player.max_shield > 0:
            safe(canvas.create_rectangle, 20, 42, 220, 54, fill=COLORS["panel"], outline=COLORS["blue"])
            sp = player.shield / max(1, player.max_shield)
            safe(canvas.create_rectangle, 20, 42, 20 + int(200 * sp), 54, fill=COLORS["blue"], outline="")
        safe(canvas.create_text, W - 20, 28, text=f"Enemies: {enemies_left}",
             fill=COLORS["text"], font=("Courier New", 11), anchor="e")
        safe(canvas.create_text, 20, H - 30, text="Laser [Space/LMB]  Missile [RMB/Shift]",
             fill=COLORS["muted"], font=("Courier New", 10), anchor="w")
        if boss and boss.alive:
            bx = W // 2 - 150
            safe(canvas.create_text, W // 2, 50, text="BOSS", fill=COLORS["danger"], font=("Arial", 12, "bold"))
            safe(canvas.create_rectangle, bx, 58, bx + 300, 72, fill=COLORS["panel"], outline=COLORS["danger"])
            pct = boss.hp / boss.max_hp
            safe(canvas.create_rectangle, bx, 58, bx + int(300 * pct), 72, fill=COLORS["danger"], outline="")
        # Minimap
        mx, my, ms = W - 140, H - 140, 120
        safe(canvas.create_rectangle, mx, my, mx + ms, my + ms, fill=COLORS["panel"], outline=COLORS["cyan"])
        safe(canvas.create_oval, mx + ms // 2 - 3, my + ms - 10, mx + ms // 2 + 3, my + ms - 4,
             fill=COLORS["cyan"], outline="")


class CombatGame:
    """Combat loop and wave manager."""

    def __init__(self, canvas, session, on_end):
        self.canvas = canvas
        self.session = session
        self.on_end = on_end
        self.player = PlayerShip(session, session.get("ship_id", "falcon"))
        self.enemies = []
        self.projectiles = []
        self.explosions = []
        self.loot = []
        self.wave = 1
        self.state = "playing"
        self.intermission = 0.0
        self.kills = 0
        self.keys = set()
        self.mouse = (W / 2, H / 2)
        self.fire_pri = self.fire_sec = False
        self._spawn_wave()

    def _spawn_wave(self):
        self.enemies.clear()
        if self.wave % 5 == 0:
            self.enemies.append(EnemyShip(W / 2, 80, "boss", self.wave))
            return
        n = 4 + self.wave * 2
        for i in range(n):
            etype = "drone"
            if self.wave >= 3 and i % 2 == 0:
                etype = "frigate"
            if self.wave >= 4 and i % 4 == 0:
                etype = "cruiser"
            self.enemies.append(EnemyShip(random.uniform(80, W - 80), random.uniform(40, 200), etype, self.wave))

    def update(self, dt):
        if self.state == "intermission":
            self.intermission -= dt
            if self.intermission <= 0:
                self.wave += 1
                self._spawn_wave()
                self.state = "playing"
            return
        if self.state != "playing":
            return
        shots = self.player.update(dt, self.keys, self.mouse, self.fire_pri, self.fire_sec)
        self.projectiles.extend(shots)
        for e in self.enemies:
            if e.alive:
                self.projectiles.extend(e.update(dt, self.player))
        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if p.alive]

        for p in self.projectiles:
            if p.owner == "player":
                for e in self.enemies:
                    if e.alive and _hit(p.bbox(), e.bbox()):
                        p.alive = False
                        e.hp -= p.damage
                        if e.hp <= 0:
                            e.alive = False
                            self.kills += 1
                            self._drop_loot(e.x, e.y)
                            self.explosions.append(Explosion(e.x, e.y))
                        break
            else:
                if _hit(p.bbox(), self.player.bbox()) and self.player.stealth_timer <= 0:
                    p.alive = False
                    if self.player.shield > 0:
                        self.player.shield -= p.damage
                    else:
                        self.player.hull -= p.damage

        for item in self.loot:
            if item.alive and _hit(item.bbox(), self.player.bbox()):
                item.alive = False
                self._collect_loot(item)

        for ex in self.explosions:
            ex.update(dt)
        self.explosions = [ex for ex in self.explosions if ex.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        if self.player.hull <= 0 and self.state == "playing":
            self.state = "defeat"
            self._finish()
        elif not self.enemies and self.state == "playing":
            self.state = "intermission"
            self.intermission = 4.0

    def _drop_loot(self, x, y):
        self.loot.append(Loot(x, y, "credits", random.randint(5, 20)))
        if random.random() < 0.3:
            self.loot.append(Loot(x + 10, y, "fuel"))
        if random.random() < 0.2:
            self.loot.append(Loot(x - 10, y, "cargo"))
        if random.random() < 0.1:
            self.loot.append(Loot(x, y + 10, "part"))
        if random.random() < 0.02:
            self.loot.append(Loot(x, y - 10, "blueprint"))

    def _collect_loot(self, item):
        if item.ltype == "credits":
            self.session["loot_credits"] = self.session.get("loot_credits", 0) + item.value
        elif item.ltype == "fuel":
            self.session["fuel"] = min(self.session.get("max_fuel", 100),
                                       self.session.get("fuel", 0) + 15)

    def _finish(self):
        if self.state == "done":
            return
        victory = self.state != "defeat"
        self.session["hull"] = max(0, self.player.hull)
        self.state = "done"
        self.on_end({
            "victory": victory,
            "kills": self.kills,
            "credits": self.session.get("loot_credits", 0),
            "loot": {},
        })

    def draw(self):
        safe(self.canvas.delete, "all")
        for e in self.enemies:
            e.draw(self.canvas)
        self.player.draw(self.canvas)
        for p in self.projectiles:
            p.draw(self.canvas)
        for item in self.loot:
            item.draw(self.canvas)
        for ex in self.explosions:
            ex.draw(self.canvas)
        boss = next((e for e in self.enemies if e.etype == "boss"), None)
        HUD.draw(self.canvas, self.player, self.wave, len(self.enemies), boss)
        if self.state == "intermission":
            safe(self.canvas.create_rectangle, 0, 0, W, H, fill="#050818", outline="")
            safe(self.canvas.create_text, W // 2, H // 2,
                 text=f"WAVE {self.wave + 1} INCOMING", fill=COLORS["cyan"],
                 font=("Arial", 24, "bold"))


def _hit(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


class CombatWindow:
    def __init__(self, parent, username, session, on_end=None):
        self.parent = parent
        self.username = username
        self.on_end = on_end
        self._loop_after = None

        self.window = tk.Toplevel(parent)
        self.window.title("Combat")
        self.window.configure(bg=COLORS["bg"])
        self.window.geometry(f"{W}x{H}")
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self._abort)

        self.canvas = tk.Canvas(self.window, width=W, height=H, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        session = dict(session)
        session["ship_id"] = get_user_data_ship(username)
        session["loot_credits"] = 0

        def finished(result):
            if on_end:
                on_end(result)

        self.combat = CombatGame(self.canvas, session, finished)
        self.canvas.bind("<KeyPress>", self._keydown)
        self.canvas.bind("<KeyRelease>", self._keyup)
        self.canvas.bind("<Motion>", self._motion)
        self.canvas.bind("<ButtonPress-1>", lambda e: setattr(self.combat, "fire_pri", True))
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self.combat, "fire_pri", False))
        self.canvas.bind("<ButtonPress-3>", lambda e: setattr(self.combat, "fire_sec", True))
        self.canvas.bind("<ButtonRelease-3>", lambda e: setattr(self.combat, "fire_sec", False))
        self.canvas.focus_set()
        self._loop()

    def _keydown(self, e):
        k = e.keysym.lower() if len(e.keysym) == 1 else e.keysym
        self.combat.keys.add(k)
        if k == "space":
            self.combat.fire_pri = True
        if k in ("Shift_L", "Shift_R"):
            self.combat.fire_sec = True

    def _keyup(self, e):
        k = e.keysym.lower() if len(e.keysym) == 1 else e.keysym
        self.combat.keys.discard(k)
        if k == "space":
            self.combat.fire_pri = False

    def _motion(self, e):
        self.combat.mouse = (e.x, e.y)

    def _loop(self):
        if not self.canvas.winfo_exists():
            return
        self.combat.update(0.016)
        self.combat.draw()
        if self.combat.state == "done":
            self._cancel_loop()
            self.window.destroy()
            return
        self._loop_after = self.window.after(16, self._loop)

    def _cancel_loop(self):
        if self._loop_after:
            try:
                self.canvas.after_cancel(self._loop_after)
            except tk.TclError:
                pass
            self._loop_after = None

    def _abort(self):
        self._cancel_loop()
        self.window.destroy()


def get_user_data_ship(username):
    from databaselogic import get_user_data
    return get_user_data(username).get("selected_ship", "falcon")
