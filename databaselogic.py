"""
databaselogic.py — Stateless account and progression logic.
"""

import bcrypt

import database


def _find_user(username):
    key = username.strip().lower()
    for user in database.users:
        if user.get("username", "").lower() == key:
            _ensure_defaults(user)
            return user
    return None


def _ensure_defaults(user):
    defaults = {
        "credits": 500,
        "highscore": 0,
        "selected_ship": "falcon",
        "commander_title": "Commander",
        "ship_upgrades": dict(database.DEFAULT_UPGRADES),
        "faction_rep": dict(database.DEFAULT_FACTION_REP),
        "discovered_systems": [0],
        "session": database.default_session("falcon"),
    }
    changed = False
    for k, v in defaults.items():
        if k not in user:
            user[k] = v if not isinstance(v, dict) else dict(v)
            changed = True
    if changed:
        database.save_data()


def username_exists(username):
    return _find_user(username) is not None


def create_user(username, password, commander_title="Commander"):
    if username_exists(username):
        return False
    try:
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except (ValueError, TypeError, AttributeError):
        return False
    ship = "falcon"
    user = {
        "username": username.strip(),
        "password_hash": pw_hash,
        "credits": 500,
        "highscore": 0,
        "selected_ship": ship,
        "commander_title": commander_title,
        "ship_upgrades": dict(database.DEFAULT_UPGRADES),
        "faction_rep": dict(database.DEFAULT_FACTION_REP),
        "discovered_systems": [0],
        "session": database.default_session(ship),
    }
    database.users.append(user)
    key = username.strip().lower()
    database.galaxy_state[key] = database.generate_galaxy(username)
    database.save_data()
    return True


def verify_login(username, password):
    user = _find_user(username)
    if not user:
        return False
    pw = user.get("password_hash") or user.get("password", "")
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            pw.encode("utf-8"),
        )
    except (ValueError, TypeError, AttributeError):
        return False


def get_user_data(username):
    user = _find_user(username)
    if not user:
        return {}
    return {
        "username": user["username"],
        "credits": user.get("credits", 0),
        "highscore": user.get("highscore", 0),
        "selected_ship": user.get("selected_ship", "falcon"),
        "commander_title": user.get("commander_title", "Commander"),
        "ship_upgrades": dict(user.get("ship_upgrades", database.DEFAULT_UPGRADES)),
        "faction_rep": dict(user.get("faction_rep", database.DEFAULT_FACTION_REP)),
        "discovered_systems": list(user.get("discovered_systems", [0])),
        "session": dict(user.get("session", database.default_session())),
    }


def save_user_data(username, data):
    user = _find_user(username)
    if not user:
        return False
    for key in (
        "credits", "highscore", "selected_ship", "commander_title",
        "ship_upgrades", "faction_rep", "discovered_systems", "session",
    ):
        if key in data:
            user[key] = data[key]
    database.save_data()
    return True


def update_highscore(username, score):
    user = _find_user(username)
    if not user:
        return False
    score = int(score)
    if score > user.get("highscore", 0):
        user["highscore"] = score
        database.save_data()
    return True


def add_credits(username, amount):
    user = _find_user(username)
    if not user:
        return False
    user["credits"] = user.get("credits", 0) + int(amount)
    database.save_data()
    return True


def set_selected_ship(username, ship_id):
    user = _find_user(username)
    if not user:
        return False
    user["selected_ship"] = ship_id
    sess = user.get("session", database.default_session(ship_id))
    hull_map = {"falcon": 100, "interceptor": 70, "dreadnought": 150, "merchant": 90, "phantom": 85}
    base = hull_map.get(ship_id, 100)
    sess["max_hull"] = base + user.get("ship_upgrades", {}).get("hull", 0) * 20
    sess["hull"] = min(sess.get("hull", base), sess["max_hull"])
    user["session"] = sess
    database.save_data()
    return True


def apply_upgrade(username, upgrade_key):
    """Purchase next tier for upgrade_key. Returns True on success."""
    user = _find_user(username)
    if not user:
        return False
    costs = [500, 1200, 2800, 6000, 12000]
    upgrades = user.setdefault("ship_upgrades", dict(database.DEFAULT_UPGRADES))
    tier = upgrades.get(upgrade_key, 0)
    if tier >= 5:
        return False
    cost = costs[tier]
    if user.get("credits", 0) < cost:
        return False
    user["credits"] -= cost
    upgrades[upgrade_key] = tier + 1
    if upgrade_key == "hull":
        sess = user.setdefault("session", database.default_session(user["selected_ship"]))
        sess["max_hull"] = _hull_max(user)
        sess["hull"] = min(sess.get("hull", sess["max_hull"]), sess["max_hull"])
    if upgrade_key == "cargo":
        sess = user.setdefault("session", database.default_session(user["selected_ship"]))
        sess["cargo_capacity"] = 20 + upgrades["cargo"] * 5
    database.save_data()
    return True


def _hull_max(user):
    ship = user.get("selected_ship", "falcon")
    base = {"falcon": 100, "interceptor": 70, "dreadnought": 150, "merchant": 90, "phantom": 85}.get(ship, 100)
    return base + user.get("ship_upgrades", {}).get("hull", 0) * 20


def update_faction_rep(username, faction_id, delta):
    user = _find_user(username)
    if not user:
        return False
    rep = user.setdefault("faction_rep", dict(database.DEFAULT_FACTION_REP))
    current = rep.get(faction_id, 0)
    rep[faction_id] = max(-100, min(100, current + int(delta)))
    database.save_data()
    return True


def mark_system_discovered(username, system_id):
    user = _find_user(username)
    if not user:
        return False
    discovered = user.setdefault("discovered_systems", [0])
    if system_id not in discovered:
        discovered.append(system_id)
        database.save_data()
    return True


def get_galaxy(username):
    key = username.strip().lower()
    if key not in database.galaxy_state:
        database.galaxy_state[key] = database.generate_galaxy(username)
        database.save_data()
    return database.galaxy_state[key]
