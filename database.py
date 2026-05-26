"""
database.py — Persistent data store for STARSHIP GALACTIC FRONTIER.

Holds in-memory users and galaxy_state; load_data()/save_data() persist to game_data.py.
"""

import hashlib
import random
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parent / "game_data.py"

users = []
galaxy_state = {}

FACTIONS = ("empire", "foundation", "pirates", "guild", "ai")
ECONOMIES = ("industrial", "agricultural", "mining", "frontier", "capital")
STAR_TYPES = ("red dwarf", "yellow", "blue giant", "neutron", "binary")
COMMODITIES = (
    "ore", "fuel_cells", "food", "medicine", "weapons", "luxury",
    "tech_parts", "contraband", "artifacts", "spice", "data_chips", "nanites",
)

DEFAULT_FACTION_REP = {
    "empire": 20,
    "foundation": 20,
    "pirates": -30,
    "guild": 10,
    "ai": -80,
}

DEFAULT_UPGRADES = {
    "engine": 0,
    "hull": 0,
    "primary": 0,
    "secondary": 0,
    "shield": 0,
    "scanner": 0,
    "cargo": 0,
    "stealth": 0,
}

BASE_PRICES = {
    "industrial": {
        "ore": 40, "fuel_cells": 55, "food": 90, "medicine": 70, "weapons": 45,
        "luxury": 120, "tech_parts": 35, "contraband": 200, "artifacts": 500,
        "spice": 80, "data_chips": 50, "nanites": 180,
    },
    "agricultural": {
        "ore": 70, "fuel_cells": 60, "food": 25, "medicine": 65, "weapons": 110,
        "luxury": 95, "tech_parts": 80, "contraband": 220, "artifacts": 480,
        "spice": 30, "data_chips": 75, "nanites": 200,
    },
    "mining": {
        "ore": 20, "fuel_cells": 50, "food": 85, "medicine": 90, "weapons": 100,
        "luxury": 130, "tech_parts": 90, "contraband": 210, "artifacts": 450,
        "spice": 70, "data_chips": 85, "nanites": 60,
    },
    "frontier": {
        "ore": 55, "fuel_cells": 70, "food": 100, "medicine": 110, "weapons": 120,
        "luxury": 140, "tech_parts": 100, "contraband": 180, "artifacts": 380,
        "spice": 90, "data_chips": 95, "nanites": 150,
    },
    "capital": {
        "ore": 50, "fuel_cells": 55, "food": 55, "medicine": 55, "weapons": 70,
        "luxury": 75, "tech_parts": 60, "contraband": 250, "artifacts": 520,
        "spice": 60, "data_chips": 45, "nanites": 170,
    },
}

SYSTEM_NAMES = (
    "Acheron", "Borealis", "Cygnus Prime", "Driftmark", "Erebus", "Fomalhaut",
    "Glimmer", "Helios", "Icarus", "Juno", "Kestrel", "Luminara", "Marrow",
    "Nexus", "Orpheus", "Pallas", "Quasar Gate", "Rift Haven", "Solace",
    "Talon", "Umbra", "Vanguard", "Warden", "Xenon", "Yarrow", "Zenith",
    "Argent", "Brim", "Cinder", "Duskfall", "Ember", "Frostline", "Gale",
    "Haven", "Ironreach", "Jade", "Krypt", "Lance", "Mirage", "Nova Deep",
)


def _seed_from_username(username):
    digest = hashlib.sha256(username.lower().encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def generate_galaxy(username):
    """Procedurally generate 40 systems and hyperlanes for one commander."""
    rng = random.Random(_seed_from_username(username))
    systems = []
    faction_pool = list(FACTIONS)
    for i in range(40):
        fx = rng.uniform(80, 920)
        fy = rng.uniform(60, 640)
        faction = rng.choice(faction_pool)
        economy = rng.choice(ECONOMIES)
        if rng.random() < 0.12:
            economy = "capital"
        threat = rng.randint(1, 5)
        if economy == "frontier":
            threat = max(threat, 3)
        if faction == "ai":
            threat = min(5, threat + 1)
        prices = {}
        base = BASE_PRICES[economy]
        for commodity in COMMODITIES:
            variance = rng.uniform(0.8, 1.2)
            if economy == "frontier":
                variance *= 1.3
            prices[commodity] = int(base[commodity] * variance)
        systems.append({
            "id": i,
            "name": SYSTEM_NAMES[i],
            "x": fx,
            "y": fy,
            "faction": faction,
            "economy": economy,
            "star_type": rng.choice(STAR_TYPES),
            "threat": threat,
            "planets": rng.randint(1, 6),
            "prices": prices,
            "visited_count": 0,
        })

    lanes = []
    for i in range(40):
        distances = []
        for j in range(40):
            if i == j:
                continue
            a, b = systems[i], systems[j]
            d = math_hypot(a["x"] - b["x"], a["y"] - b["y"])
            distances.append((d, j))
        distances.sort(key=lambda t: t[0])
        for _, j in distances[:3]:
            pair = (min(i, j), max(i, j))
            if pair not in lanes:
                lanes.append(pair)

    return {"seed": _seed_from_username(username), "systems": systems, "lanes": lanes}


def math_hypot(x, y):
    return (x * x + y * y) ** 0.5


def default_session(ship_id="falcon"):
    """Starting run state for a new or reset session."""
    hull_base = {"falcon": 100, "interceptor": 70, "dreadnought": 150,
                 "merchant": 90, "phantom": 85}.get(ship_id, 100)
    return {
        "current_system": 0,
        "hull": hull_base,
        "max_hull": hull_base,
        "fuel": 100,
        "max_fuel": 100,
        "cargo": {},
        "cargo_capacity": 20,
        "credits": 0,
        "price_history": {},
        "kills": 0,
        "day": 1,
    }


def load_data():
    """Load users and galaxy_state from game_data.py."""
    global users, galaxy_state
    if not _DATA_FILE.exists():
        users = []
        galaxy_state = {}
        return
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as handle:
            namespace = {}
            exec(handle.read(), namespace)
            users = namespace.get("users", [])
            galaxy_state = namespace.get("galaxy_state", {})
            if not isinstance(users, list):
                users = []
            if not isinstance(galaxy_state, dict):
                galaxy_state = {}
    except (OSError, SyntaxError, ValueError):
        users = []
        galaxy_state = {}


def save_data():
    """Write users and galaxy_state to game_data.py."""
    header = (
        '"""\nAuto-generated game data for STARSHIP GALACTIC FRONTIER.\n"""\n\n'
    )
    with open(_DATA_FILE, "w", encoding="utf-8") as handle:
        handle.write(header)
        handle.write("users = ")
        handle.write(repr(users))
        handle.write("\n\ngalaxy_state = ")
        handle.write(repr(galaxy_state))
        handle.write("\n")


load_data()
