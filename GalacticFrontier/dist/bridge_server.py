"""
bridge_server.py — JSON-RPC stdin/stdout bridge for WPF Galactic Frontier frontend.

Reads one JSON command per line from stdin, writes one JSON response per line to stdout.
No debug output — only valid JSON responses.
"""

import json
import sys

import databaselogic


def _read_params(cmd):
    return cmd.get("parameters") or {}


def _ok(**kwargs):
    out = {"success": True}
    out.update(kwargs)
    return out


def _fail(msg):
    return {"success": False, "error": str(msg)}


def handle(cmd):
    method = cmd.get("method", "")
    p = _read_params(cmd)

    if method == "ping":
        return _ok(message="pong")

    if method == "verify_login":
        username = p.get("username", "")
        password = p.get("password", "")
        if databaselogic.verify_login(username, password):
            user = databaselogic.get_user_data(username)
            return _ok(username=user.get("username", username))
        return _fail("Invalid credentials")

    if method == "create_user":
        username = p.get("username", "")
        password = p.get("password", "")
        title = p.get("commander_title", "Commander")
        if databaselogic.username_exists(username):
            return _fail("Username taken")
        if databaselogic.create_user(username, password, title):
            return _ok()
        return _fail("Registration failed")

    if method == "username_exists":
        return _ok(exists=databaselogic.username_exists(p.get("username", "")))

    if method == "get_user_data":
        data = databaselogic.get_user_data(p.get("username", ""))
        if not data:
            return _fail("User not found")
        return _ok(data=data)

    if method == "save_user_data":
        if databaselogic.save_user_data(p.get("username", ""), p.get("data", {})):
            return _ok()
        return _fail("Save failed")

    if method == "set_selected_ship":
        ship_id = p.get("ship_id", "falcon").lower()
        if databaselogic.set_selected_ship(p.get("username", ""), ship_id):
            return _ok()
        return _fail("Could not set ship")

    if method == "get_galaxy":
        galaxy = databaselogic.get_galaxy(p.get("username", ""))
        return _ok(
            systems=galaxy.get("systems", []),
            lanes=galaxy.get("lanes", []),
        )

    if method == "add_credits":
        username = p.get("username", "")
        amount = int(p.get("amount", 0))
        if databaselogic.add_credits(username, amount):
            data = databaselogic.get_user_data(username)
            return _ok(new_balance=data.get("credits", 0))
        return _fail("Could not add credits")

    if method == "apply_upgrade":
        username = p.get("username", "")
        key = p.get("upgrade_key", "")
        if databaselogic.apply_upgrade(username, key):
            data = databaselogic.get_user_data(username)
            return _ok(upgrades=data.get("ship_upgrades", {}), credits=data.get("credits", 0))
        return _fail("Upgrade failed")

    if method == "update_faction_rep":
        username = p.get("username", "")
        faction = p.get("faction_id", "")
        delta = int(p.get("delta", 0))
        if databaselogic.update_faction_rep(username, faction, delta):
            data = databaselogic.get_user_data(username)
            rep = data.get("faction_rep", {})
            return _ok(new_rep=rep.get(faction, 0), faction_rep=rep)
        return _fail("Could not update reputation")

    if method == "update_highscore":
        username = p.get("username", "")
        score = int(p.get("score", 0))
        if databaselogic.update_highscore(username, score):
            data = databaselogic.get_user_data(username)
            return _ok(highscore=data.get("highscore", score))
        return _fail("Could not update highscore")

    if method == "mark_system_discovered":
        if databaselogic.mark_system_discovered(
            p.get("username", ""), int(p.get("system_id", 0))
        ):
            return _ok()
        return _fail("Could not mark system")

    return _fail("Unknown method")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
            result = handle(cmd)
        except json.JSONDecodeError as exc:
            result = _fail(f"Invalid JSON: {exc}")
        except Exception as exc:
            result = _fail(str(exc))
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
