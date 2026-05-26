"""
signup.py — Commander registration (Toplevel + on_success callback).
"""

import re
import tkinter as tk

from databaselogic import create_user, username_exists

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,14}$")
TITLES = ("Admiral", "Commander", "Pilot", "Rogue")


class SignupWindow:
    """Registration Toplevel; on_success(username) deferred after destroy."""

    def __init__(self, parent, username=None, on_success=None):
        self.parent = parent
        self.username = username
        self.on_success = on_success
        self._after_id = None

        from launcher import APP_CONFIG, COLORS, Starfield, safe_canvas, defer, raise_toplevel
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._Starfield = Starfield
        self._safe = safe_canvas
        self._defer = defer
        self._raise = raise_toplevel

        self.window = tk.Toplevel(parent)
        self.window.title("STARSHIP GALACTIC FRONTIER — Sign Up")
        self.window.configure(bg=COLORS["bg"])
        self.window.geometry(f"{APP_CONFIG['default_w']}x{APP_CONFIG['default_h']}")
        self.window.transient(parent)
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
            self.canvas, APP_CONFIG["default_w"], APP_CONFIG["default_h"], 120,
        )
        self.title_var = tk.StringVar(value="Commander")
        self._build_ui()
        self._tick()
        raise_toplevel(self.window)

    def _build_ui(self):
        COLORS = self._colors
        cx = self._cfg["default_w"] // 2
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, 80, text="CREATE COMMANDER PROFILE",
            fill=COLORS["cyan"], font=("Arial", 22, "bold"), tags=("ui",),
        )
        self._safe(
            self.canvas, self.canvas.create_text,
            cx - 200, 150, text="USERNAME", fill=COLORS["blue"],
            font=("Courier New", 12), anchor="w", tags=("ui",),
        )
        self.user_entry = tk.Entry(
            self.window, font=("Courier New", 12), bg=COLORS["panel"],
            fg=COLORS["text"], insertbackground=COLORS["cyan"], width=30,
        )
        self.canvas.create_window(cx, 175, window=self.user_entry, tags=("ui",))

        self._safe(
            self.canvas, self.canvas.create_text,
            cx - 200, 220, text="PASSWORD", fill=COLORS["blue"],
            font=("Courier New", 12), anchor="w", tags=("ui",),
        )
        self.pass_entry = tk.Entry(
            self.window, show="*", font=("Courier New", 12), bg=COLORS["panel"],
            fg=COLORS["text"], insertbackground=COLORS["cyan"], width=30,
        )
        self.canvas.create_window(cx, 245, window=self.pass_entry, tags=("ui",))

        show_btn = tk.Button(
            self.window, text="SHOW / HIDE", command=self._toggle_pass,
            bg=COLORS["panel"], fg=COLORS["cyan"], relief=tk.FLAT,
        )
        self.canvas.create_window(cx, 285, window=show_btn, tags=("ui",))

        self._safe(
            self.canvas, self.canvas.create_text,
            cx - 200, 320, text="COMMANDER TITLE", fill=COLORS["blue"],
            font=("Courier New", 12), anchor="w", tags=("ui",),
        )
        title_menu = tk.OptionMenu(self.window, self.title_var, *TITLES)
        title_menu.config(bg=COLORS["panel"], fg=COLORS["text"], highlightthickness=0)
        self.canvas.create_window(cx, 350, window=title_menu, tags=("ui",))

        self.err_id = self._safe(
            self.canvas, self.canvas.create_text,
            cx, 400, text="", fill=COLORS["danger"],
            font=("Courier New", 11), tags=("ui",),
        )

        submit = tk.Button(
            self.window, text="REGISTER", command=self._handle_submit,
            bg=COLORS["panel"], fg=COLORS["cyan"], font=("Arial", 11, "bold"),
            relief=tk.FLAT, highlightbackground=COLORS["cyan"], highlightthickness=1,
        )
        self.canvas.create_window(cx, 460, window=submit, tags=("ui",))

        back = tk.Button(
            self.window, text="BACK", command=self._on_close,
            bg=COLORS["panel"], fg=COLORS["muted"], relief=tk.FLAT,
        )
        self.canvas.create_window(cx, 510, window=back, tags=("ui",))

    def _toggle_pass(self):
        self.pass_entry.config(show="" if self.pass_entry.cget("show") == "*" else "*")

    def _set_error(self, msg):
        self._safe(self.canvas, self.canvas.itemconfig, self.err_id, text=msg)

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
        self._after_id = self.window.after(40, self._tick)

    def _handle_submit(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        if not USERNAME_RE.match(username):
            self._set_error("Username: 3–14 alphanumeric characters.")
            return
        if username.isdigit():
            self._set_error("Username cannot be numbers only.")
            return
        if len(password) < 8:
            self._set_error("Password must be at least 8 characters.")
            return
        if username_exists(username):
            self._set_error("Username already registered.")
            return
        if not create_user(username, password, self.title_var.get()):
            self._set_error("Registration failed. Try again.")
            return
        self._set_error("")
        self._finish_success(username)

    def _finish_success(self, username):
        self._cancel_after()
        cb = self.on_success
        parent = self.parent
        self.window.destroy()
        if cb:
            self._defer(parent, cb, username)

    def _on_close(self):
        self._cancel_after()
        self.window.destroy()
