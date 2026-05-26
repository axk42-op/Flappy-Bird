"""
game.py — Session autosave helpers and optional direct launch by username.
Uses launcher.LauncherApp (single Tk root). Run: python game.py [username]
"""

import sys

from databaselogic import get_user_data, save_user_data
from launcher import APP_CONFIG, COLORS, LauncherApp, defer, safe_canvas


class PauseOverlay:
    """Temporary pause layer on a screen that exposes .canvas."""

    def __init__(self, screen):
        self.screen = screen
        self.canvas = screen.canvas
        self.ids = []
        self._draw()
        self.canvas.bind("<Escape>", self._close, add="+")

    def _draw(self):
        w = APP_CONFIG["default_w"]
        h = APP_CONFIG["default_h"]
        r = safe_canvas(
            self.canvas, self.canvas.create_rectangle,
            0, 0, w, h, fill="#050818", outline="",
        )
        t = safe_canvas(
            self.canvas, self.canvas.create_text,
            w // 2, h // 2, text="PAUSED — ESC TO RESUME",
            fill=COLORS["cyan"], font=("Arial", 18, "bold"),
        )
        self.ids = [i for i in (r, t) if i]

    def _close(self, _event=None):
        for i in self.ids:
            safe_canvas(self.canvas, self.canvas.delete, i)


class GameApp(LauncherApp):
    """Launcher with autosave; skips menu when username provided on CLI."""

    def __init__(self, username=None):
        super().__init__()
        if username:
            self.username = username
            data = get_user_data(username)
            self.session = data.get("session", {})
            self._hide_launcher_menu()
            self.root.withdraw()
            defer(self.root, self.after_login, username)
            self._schedule_autosave()

    def autosave(self):
        if not self.username:
            return
        data = get_user_data(self.username)
        if self._galaxy_window and hasattr(self._galaxy_window, "session"):
            data["session"] = self._galaxy_window.session
            data["credits"] = self._galaxy_window.session.get("credits", data.get("credits", 0))
        elif hasattr(self, "session") and self.session:
            data["session"] = self.session
        save_user_data(self.username, data)

    def _schedule_autosave(self):
        self.autosave()
        if self.root.winfo_exists():
            self.root.after(60000, self._schedule_autosave)


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    if username:
        GameApp(username).run()
    else:
        LauncherApp().run()


if __name__ == "__main__":
    main()
