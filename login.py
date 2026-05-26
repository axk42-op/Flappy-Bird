"""
login.py — Commander login (Toplevel + on_success callback).
"""

import time
import tkinter as tk

from databaselogic import verify_login

MAX_ATTEMPTS = 3
LOCKOUT_SEC = 5


class LoginWindow:
    """Login Toplevel; destroys self then defers on_success(username)."""

    def __init__(self, parent, username=None, on_success=None, prefill=""):
        self.parent = parent
        self.username = username
        self.on_success = on_success
        self.attempts = 0
        self.locked_until = 0.0
        self._after_id = None

        from launcher import APP_CONFIG, COLORS, Starfield, safe_canvas, defer, raise_toplevel
        self._cfg = APP_CONFIG
        self._colors = COLORS
        self._Starfield = Starfield
        self._safe = safe_canvas
        self._defer = defer
        self._raise = raise_toplevel

        self.window = tk.Toplevel(parent)
        self.window.title("STARSHIP GALACTIC FRONTIER — Login")
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
        self._build_ui(prefill)
        self._tick()
        raise_toplevel(self.window)

    def _build_ui(self, prefill):
        COLORS = self._colors
        cx = self._cfg["default_w"] // 2
        self._safe(
            self.canvas, self.canvas.create_text,
            cx, 90, text="COMMANDER LOGIN", fill=COLORS["cyan"],
            font=("Arial", 22, "bold"), tags=("ui",),
        )
        self._safe(
            self.canvas, self.canvas.create_text,
            cx - 200, 170, text="USERNAME", fill=COLORS["blue"],
            font=("Courier New", 12), anchor="w", tags=("ui",),
        )
        self.user_entry = tk.Entry(
            self.window, font=("Courier New", 12), bg=COLORS["panel"],
            fg=COLORS["text"], insertbackground=COLORS["cyan"], width=30,
        )
        self.user_entry.insert(0, prefill)
        self.canvas.create_window(cx, 195, window=self.user_entry, tags=("ui",))

        self._safe(
            self.canvas, self.canvas.create_text,
            cx - 200, 240, text="PASSWORD", fill=COLORS["blue"],
            font=("Courier New", 12), anchor="w", tags=("ui",),
        )
        self.pass_entry = tk.Entry(
            self.window, show="*", font=("Courier New", 12), bg=COLORS["panel"],
            fg=COLORS["text"], insertbackground=COLORS["cyan"], width=30,
        )
        self.canvas.create_window(cx, 265, window=self.pass_entry, tags=("ui",))

        toggle = tk.Button(
            self.window, text="SHOW / HIDE", command=self._toggle,
            bg=COLORS["panel"], fg=COLORS["cyan"], relief=tk.FLAT,
        )
        self.canvas.create_window(cx, 305, window=toggle, tags=("ui",))

        self.err_id = self._safe(
            self.canvas, self.canvas.create_text,
            cx, 350, text="", fill=COLORS["danger"],
            font=("Courier New", 11), tags=("ui",),
        )

        submit = tk.Button(
            self.window, text="AUTHENTICATE", command=self._handle_submit,
            bg=COLORS["panel"], fg=COLORS["cyan"], font=("Arial", 11, "bold"),
            relief=tk.FLAT, highlightbackground=COLORS["cyan"], highlightthickness=1,
        )
        self.canvas.create_window(cx, 420, window=submit, tags=("ui",))

        back = tk.Button(
            self.window, text="BACK", command=self._on_close,
            bg=COLORS["panel"], fg=COLORS["muted"], relief=tk.FLAT,
        )
        self.canvas.create_window(cx, 470, window=back, tags=("ui",))

        self.window.bind("<Return>", lambda e: self._handle_submit())

    def _toggle(self):
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
        if time.time() < self.locked_until:
            left = int(self.locked_until - time.time()) + 1
            self._set_error(f"LOCKOUT — retry in {left}s")
            return
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        if verify_login(username, password):
            self._set_error("")
            self._finish_success(username)
            return
        self.attempts += 1
        remaining = MAX_ATTEMPTS - self.attempts
        if remaining <= 0:
            self.locked_until = time.time() + LOCKOUT_SEC
            self.attempts = 0
            self._set_error(f"ACCESS DENIED — lockout {LOCKOUT_SEC}s")
        else:
            self._set_error(f"Invalid credentials. {remaining} attempt(s) left.")

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
