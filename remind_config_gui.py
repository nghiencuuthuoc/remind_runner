
# remind_config_gui.py
# PharmApp-themed Tkinter GUI to configure reminders.toml for remind_runner.py
# - No external dependencies (uses Python 3.11+ 'tomllib' to read TOML)
# - Edit timezone, sound_file, and task list (time/type/message/command/days/enabled/sound)
# - Keyboard shortcuts: Ctrl+O (Open), Ctrl+S (Save), Ctrl+Shift+S (Save As), F2 (Add),
#   Ctrl+D (Duplicate), Delete (Remove), Alt+Up/Alt+Down (Reorder)
#
# Usage:
#   python remind_config_gui.py --config reminders.toml
#
# Works nicely with the companion runner: remind_runner.py

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import tomllib  # Python 3.11+ for reading TOML
except Exception:
    tomllib = None

# ----------------------------- Utilities & Model -----------------------------

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

DAYS_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_LABELS = {
    "Mon": "Mon (T2)",
    "Tue": "Tue (T3)",
    "Wed": "Wed (T4)",
    "Thu": "Thu (T5)",
    "Fri": "Fri (T6)",
    "Sat": "Sat (T7)",
    "Sun": "Sun (CN)",
}

@dataclass
class Task:
    time: str = "08:00"
    type: str = "notify"      # "notify" | "command" | "both"
    message: str = "Reminder"
    command: Optional[str] = ""
    days: List[str] = field(default_factory=list)  # e.g. ["Mon","Tue","Wed","Thu","Fri"]
    enabled: bool = True
    sound: bool = True

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Task":
        return Task(
            time=str(d.get("time", "08:00")),
            type=str(d.get("type", "notify")),
            message=str(d.get("message", "Reminder")),
            command=d.get("command", "") or "",
            days=list(d.get("days", []) or []),
            enabled=bool(d.get("enabled", True)),
            sound=bool(d.get("sound", True)),
        )

    def to_toml_block(self) -> str:
        def esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\"')
        lines = []
        lines.append("[[task]]")
        lines.append(f'time = "{esc(self.time)}"')
        lines.append(f'type = "{esc(self.type)}"')
        lines.append(f'message = "{esc(self.message)}"')
        if self.command:
            lines.append(f'command = "{esc(self.command)}"')
        if self.days:
            day_items = ", ".join([f'"{esc(d)}"' for d in self.days])
            lines.append(f"days = [{day_items}]")
        lines.append(f"enabled = {'true' if self.enabled else 'false'}")
        lines.append(f"sound = {'true' if self.sound else 'false'}")
        return "\n".join(lines)

@dataclass
class Config:
    timezone: str = "Asia/Ho_Chi_Minh"
    sound_file: str = ""
    tasks: List[Task] = field(default_factory=list)

    @staticmethod
    def from_toml_text(text: str) -> "Config":
        if tomllib is None:
            raise RuntimeError("Python 3.11+ is required to read TOML (needs tomllib).")
        d = tomllib.loads(text)
        tz = d.get("timezone", "Asia/Ho_Chi_Minh")
        sf = d.get("sound_file", "") or ""
        raw_tasks = d.get("task", []) or d.get("tasks", []) or []
        tasks = [Task.from_dict(t) for t in raw_tasks]
        return Config(timezone=tz, sound_file=sf, tasks=tasks)

    def to_toml_text(self) -> str:
        def esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\"')
        lines = []
        lines.append(f'timezone = "{esc(self.timezone)}"')
        lines.append(f'sound_file = "{esc(self.sound_file)}"')
        lines.append("")
        for t in self.tasks:
            lines.append(t.to_toml_block())
            lines.append("")
        return "\n".join(lines).strip() + "\n"

# ----------------------------- Theming -----------------------------

def apply_pharmapp_theme(root: tk.Tk) -> None:
    # Colors from user’s preference
    BG = "#fdf5e6"    # warm background
    FG = "#2a2a2a"    # primary text
    ACCENT = "#f4a261"  # orange
    ACCENT_DARK = "#e76f51"  # darker

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)

    style.configure(".", background=BG, foreground=FG, fieldbackground="white")
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("TFrame", background=BG)
    style.configure("TLabelframe", background=BG, foreground=FG)
    style.configure("TLabelframe.Label", background=BG, foreground=FG)
    style.configure("TEntry", padding=4)
    style.configure("TButton", padding=6)
    style.map("TButton",
              background=[("active", ACCENT), ("!active", ACCENT)],
              foreground=[("active", "white"), ("!active", "white")])

    style.configure("Accent.TButton", padding=8, relief="flat")
    style.map("Accent.TButton",
              background=[("active", ACCENT_DARK), ("!active", ACCENT)],
              foreground=[("active", "white"), ("!active", "white")])

    style.configure("TCheckbutton", background=BG, foreground=FG)

# ----------------------------- GUI -----------------------------

class ReminderConfigApp(tk.Tk):
    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()
        self.title("PharmApp • Reminder Config")
        self.geometry("1100x680")
        self.minsize(1000, 600)
        apply_pharmapp_theme(self)

        self.config_path: Optional[Path] = config_path
        self.config: Config = Config()

        # ----- Top: File row -----
        top = ttk.Frame(self)
        top.pack(fill="x", padx=14, pady=(14, 8))

        self.var_path = tk.StringVar(value=str(self.config_path) if self.config_path else "")
        ttk.Label(top, text="Config file (.toml):").pack(side="left")
        self.ent_path = ttk.Entry(top, textvariable=self.var_path, width=70)
        self.ent_path.pack(side="left", padx=8)
        ttk.Button(top, text="Browse", command=self.on_browse).pack(side="left", padx=4)
        ttk.Button(top, text="Reload", command=self.on_reload).pack(side="left", padx=4)
        ttk.Button(top, text="Save", style="Accent.TButton", command=self.on_save).pack(side="left", padx=6)
        ttk.Button(top, text="Save As…", command=self.on_save_as).pack(side="left", padx=4)

        # ----- Middle: Split pane -----
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=14, pady=8)

        # Left: Task list and controls
        left = ttk.Frame(mid)
        left.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(left, text="Tasks").pack(anchor="w")
        self.lst_tasks = tk.Listbox(left, height=25, activestyle="dotbox")
        self.lst_tasks.pack(fill="y", expand=False)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="➕ Add (F2)", command=self.on_add).pack(side="left", padx=2)
        ttk.Button(btns, text="⎘ Duplicate (Ctrl+D)", command=self.on_duplicate).pack(side="left", padx=2)
        ttk.Button(btns, text="🗑 Delete (Del)", command=self.on_delete).pack(side="left", padx=2)

        btns2 = ttk.Frame(left)
        btns2.pack(fill="x", pady=(2, 0))
        ttk.Button(btns2, text="▲ Up (Alt+↑)", command=lambda: self.on_move(-1)).pack(side="left", padx=2)
        ttk.Button(btns2, text="▼ Down (Alt+↓)", command=lambda: self.on_move(1)).pack(side="left", padx=2)

        # Right: Editor and global settings
        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True)

        # Global settings
        gf = ttk.Labelframe(right, text="Global settings")
        gf.pack(fill="x", pady=(0, 8))

        self.var_timezone = tk.StringVar(value="Asia/Ho_Chi_Minh")
        self.var_sound_file = tk.StringVar(value="")

        row = ttk.Frame(gf); row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Timezone:").pack(side="left")
        ttk.Entry(row, textvariable=self.var_timezone, width=30).pack(side="left", padx=6)
        ttk.Label(row, text="(e.g., Asia/Ho_Chi_Minh)").pack(side="left")

        row2 = ttk.Frame(gf); row2.pack(fill="x", padx=8, pady=4)
        ttk.Label(row2, text="Sound file:").pack(side="left")
        ttk.Entry(row2, textvariable=self.var_sound_file, width=50).pack(side="left", padx=6)
        ttk.Button(row2, text="Pick…", command=self.on_pick_sound).pack(side="left", padx=4)
        ttk.Button(row2, text="Test sound", command=self.on_test_sound).pack(side="left", padx=4)

        # Task editor
        tf = ttk.Labelframe(right, text="Task editor")
        tf.pack(fill="both", expand=True)

        # Row 1: time, type
        r1 = ttk.Frame(tf); r1.pack(fill="x", padx=8, pady=6)
        self.var_time = tk.StringVar()
        self.var_type = tk.StringVar(value="notify")
        ttk.Label(r1, text="Time (HH:MM):").pack(side="left")
        ttk.Entry(r1, textvariable=self.var_time, width=10).pack(side="left", padx=6)
        ttk.Label(r1, text="Type:").pack(side="left", padx=(14,0))
        self.cmb_type = ttk.Combobox(r1, textvariable=self.var_type, values=["notify", "command", "both"], width=10, state="readonly")
        self.cmb_type.pack(side="left", padx=6)

        # Row 2: message
        r2 = ttk.Frame(tf); r2.pack(fill="x", padx=8, pady=6)
        self.var_message = tk.StringVar()
        ttk.Label(r2, text="Message:").pack(side="left")
        ttk.Entry(r2, textvariable=self.var_message, width=70).pack(side="left", padx=6, fill="x", expand=True)

        # Row 3: command
        r3 = ttk.Frame(tf); r3.pack(fill="x", padx=8, pady=6)
        self.var_command = tk.StringVar()
        ttk.Label(r3, text="Command:").pack(side="left")
        ttk.Entry(r3, textvariable=self.var_command, width=70).pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(r3, text="Browse…", command=self.on_pick_command).pack(side="left", padx=4)

        # Row 4: days checkboxes
        r4 = ttk.Frame(tf); r4.pack(fill="x", padx=8, pady=6)
        ttk.Label(r4, text="Days:").pack(side="left")
        self.day_vars: Dict[str, tk.BooleanVar] = {d: tk.BooleanVar() for d in DAYS_ORDER}
        for d in DAYS_ORDER:
            ttk.Checkbutton(r4, text=DAY_LABELS[d], variable=self.day_vars[d]).pack(side="left", padx=3)

        # Row 5: toggles
        r5 = ttk.Frame(tf); r5.pack(fill="x", padx=8, pady=6)
        self.var_enabled = tk.BooleanVar(value=True)
        self.var_sound = tk.BooleanVar(value=True)
        ttk.Checkbutton(r5, text="Enabled", variable=self.var_enabled).pack(side="left")
        ttk.Checkbutton(r5, text="Play sound", variable=self.var_sound).pack(side="left", padx=14)

        # Quick day sets
        r6 = ttk.Frame(tf); r6.pack(fill="x", padx=8, pady=6)
        ttk.Button(r6, text="Every day", command=lambda: self.set_days("all")).pack(side="left", padx=2)
        ttk.Button(r6, text="Weekdays", command=lambda: self.set_days("weekdays")).pack(side="left", padx=2)
        ttk.Button(r6, text="Weekend", command=lambda: self.set_days("weekend")).pack(side="left", padx=2)
        ttk.Button(r6, text="Clear", command=lambda: self.set_days("clear")).pack(side="left", padx=2)

        # Apply / Revert buttons for the selected task
        r7 = ttk.Frame(tf); r7.pack(fill="x", padx=8, pady=(8, 10))
        ttk.Button(r7, text="Apply to selected", style="Accent.TButton", command=self.on_apply_to_selected).pack(side="left", padx=4)
        ttk.Button(r7, text="Revert fields", command=self.on_revert_fields).pack(side="left", padx=4)

        # Bottom: Status bar
        bottom = ttk.Frame(self, relief="flat")
        bottom.pack(fill="x", padx=14, pady=(0, 10))
        self.var_status = tk.StringVar(value="Ready.")
        self.lbl_status = ttk.Label(bottom, textvariable=self.var_status)
        self.lbl_status.pack(side="left")

        # Bind events
        self.lst_tasks.bind("<<ListboxSelect>>", lambda e: self.populate_fields_from_selected())
        self.bind("<F2>", lambda e: self.on_add())
        self.bind("<Delete>", lambda e: self.on_delete())
        self.bind("<Control-s>", lambda e: self.on_save())
        self.bind("<Control-S>", lambda e: self.on_save())
        self.bind("<Control-Shift-S>", lambda e: self.on_save_as())
        self.bind("<Control-o>", lambda e: self.on_browse())
        self.bind("<Control-O>", lambda e: self.on_browse())
        self.bind("<Alt-Up>", lambda e: self.on_move(-1))
        self.bind("<Alt-Down>", lambda e: self.on_move(1))
        self.bind("<Control-d>", lambda e: self.on_duplicate())
        self.bind("<Control-D>", lambda e: self.on_duplicate())

        # Initial load
        if self.config_path and self.config_path.exists():
            self.load_from_file(self.config_path)
        else:
            # start with one helpful example task
            self.config.tasks = [
                Task(time="07:30", type="both", message="Chạy file FSP", command="python E:/path/to/fsp.py", days=["Mon","Tue","Wed","Thu","Fri"], enabled=True, sound=True),
                Task(time="15:00", type="notify", message="Ghi báo cáo hằng ngày", command="", days=[], enabled=True, sound=True),
            ]
            self.refresh_task_list()
            self.populate_fields_from_selected(select_index=0)

    # ----------------------------- File ops -----------------------------
    def on_browse(self):
        p = filedialog.askopenfilename(title="Open reminders.toml", filetypes=[("TOML files", "*.toml"), ("All files", "*.*")])
        if not p:
            return
        self.var_path.set(p)
        self.config_path = Path(p)
        self.load_from_file(self.config_path)

    def on_reload(self):
        if not self.config_path or not self.config_path.exists():
            messagebox.showinfo("Reload", "No config file selected yet.")
            return
        self.load_from_file(self.config_path)

    def on_save(self):
        if not self.config_path:
            return self.on_save_as()
        try:
            self.apply_current_fields_if_needed()
            text = self.config.to_toml_text()
            self.config_path.write_text(text, encoding="utf-8")
            self.set_status(f"Saved: {self.config_path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def on_save_as(self):
        p = filedialog.asksaveasfilename(title="Save reminders.toml as…", defaultextension=".toml", filetypes=[("TOML files", "*.toml")])
        if not p:
            return
        self.var_path.set(p)
        self.config_path = Path(p)
        self.on_save()

    def load_from_file(self, path: Path):
        try:
            txt = path.read_text(encoding="utf-8")
            cfg = Config.from_toml_text(txt)
        except Exception as e:
            messagebox.showerror("Load error", f"Failed to load TOML: {e}")
            return
        self.config = cfg
        self.var_timezone.set(self.config.timezone)
        self.var_sound_file.set(self.config.sound_file)
        self.refresh_task_list()
        self.populate_fields_from_selected(select_index=0)
        self.set_status(f"Loaded: {path}")

    # ----------------------------- Task list ops -----------------------------
    def refresh_task_list(self):
        self.lst_tasks.delete(0, tk.END)
        for i, t in enumerate(self.config.tasks):
            self.lst_tasks.insert(tk.END, f"{t.time} • {t.type} • {t.message[:50]}")

    def populate_fields_from_selected(self, select_index: Optional[int] = None):
        idx = select_index
        if idx is None:
            sel = self.lst_tasks.curselection()
            if not sel:
                return
            idx = sel[0]
        if idx < 0 or idx >= len(self.config.tasks):
            return
        t = self.config.tasks[idx]
        # Globals (keep in sync)
        self.var_timezone.set(self.config.timezone)
        self.var_sound_file.set(self.config.sound_file)
        # Task fields
        self.var_time.set(t.time)
        self.var_type.set(t.type)
        self.var_message.set(t.message)
        self.var_command.set(t.command or "")
        for d in DAYS_ORDER:
            self.day_vars[d].set(d in (t.days or []))
        self.var_enabled.set(t.enabled)
        self.var_sound.set(t.sound)
        # Ensure selection reflects idx
        self.lst_tasks.selection_clear(0, tk.END)
        self.lst_tasks.selection_set(idx)
        self.lst_tasks.see(idx)

    def apply_current_fields_if_needed(self):
        sel = self.lst_tasks.curselection()
        if not sel:
            return
        idx = sel[0]
        self.apply_fields_to_task(idx)

    def on_apply_to_selected(self):
        sel = self.lst_tasks.curselection()
        if not sel:
            messagebox.showinfo("Apply", "Please select a task on the left.")
            return
        self.apply_fields_to_task(sel[0])

    def on_revert_fields(self):
        self.populate_fields_from_selected()

    def apply_fields_to_task(self, idx: int):
        # Validate time
        tstr = self.var_time.get().strip()
        if not TIME_RE.match(tstr):
            messagebox.showwarning("Invalid time", "Time must be in 24h HH:MM format.")
            return
        # Validate type
        ttype = self.var_type.get().strip()
        if ttype not in ("notify", "command", "both"):
            messagebox.showwarning("Invalid type", "Type must be one of: notify, command, both.")
            return
        # Update globals
        self.config.timezone = self.var_timezone.get().strip() or "Asia/Ho_Chi_Minh"
        self.config.sound_file = self.var_sound_file.get().strip()

        # Update task
        t = self.config.tasks[idx]
        t.time = tstr
        t.type = ttype
        t.message = self.var_message.get().strip()
        t.command = self.var_command.get().strip()
        t.days = [d for d in DAYS_ORDER if self.day_vars[d].get()]
        t.enabled = bool(self.var_enabled.get())
        t.sound = bool(self.var_sound.get())

        self.refresh_task_list()
        self.populate_fields_from_selected(select_index=idx)
        self.set_status("Applied changes to selected task.")

    def on_add(self):
        self.config.tasks.append(Task())
        self.refresh_task_list()
        self.populate_fields_from_selected(select_index=len(self.config.tasks)-1)
        self.set_status("Added new task.")

    def on_duplicate(self):
        sel = self.lst_tasks.curselection()
        if not sel:
            return
        idx = sel[0]
        src = self.config.tasks[idx]
        dup = Task.from_dict(asdict(src))
        self.config.tasks.insert(idx+1, dup)
        self.refresh_task_list()
        self.populate_fields_from_selected(select_index=idx+1)
        self.set_status("Duplicated task.")

    def on_delete(self):
        sel = self.lst_tasks.curselection()
        if not sel:
            return
        idx = sel[0]
        if messagebox.askyesno("Delete task", "Are you sure you want to delete the selected task?"):
            del self.config.tasks[idx]
            self.refresh_task_list()
            if self.config.tasks:
                self.populate_fields_from_selected(select_index=min(idx, len(self.config.tasks)-1))
            self.set_status("Deleted task.")

    def on_move(self, delta: int):
        sel = self.lst_tasks.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self.config.tasks):
            return
        self.config.tasks[idx], self.config.tasks[new_idx] = self.config.tasks[new_idx], self.config.tasks[idx]
        self.refresh_task_list()
        self.populate_fields_from_selected(select_index=new_idx)
        self.set_status("Reordered task.")

    def set_days(self, mode: str):
        sets = {
            "all": DAYS_ORDER,
            "weekdays": DAYS_ORDER[:5],
            "weekend": DAYS_ORDER[5:],
            "clear": [],
        }
        on = set(sets.get(mode, []))
        for d in DAYS_ORDER:
            self.day_vars[d].set(d in on)

    # ----------------------------- Pickers & Sound helpers -----------------------------
    def on_pick_sound(self):
        p = filedialog.askopenfilename(title="Pick sound file", filetypes=[("Audio", "*.wav *.aiff *.aif *.mp3"), ("All files", "*.*")])
        if p:
            self.var_sound_file.set(p)

    def on_test_sound(self):
        self.play_sound(self.var_sound_file.get().strip() or None)

    def on_pick_command(self):
        # Allow selecting scripts or executables; keep text editable so users can prepend 'python ' if needed.
        p = filedialog.askopenfilename(
            title="Pick command/script to run",
            filetypes=[
                ("Programs/Scripts", "*.exe *.bat *.cmd *.py *.ps1 *.sh"),
                ("All files", "*.*"),
            ]
        )
        if p:
            self.var_command.set(p)

    @staticmethod
    def play_sound(sound_file: Optional[str] = None):
        # Windows
        if sys.platform.startswith("win"):
            try:
                import winsound
                if sound_file and Path(sound_file).exists():
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return
            except Exception:
                pass
        # macOS
        if shutil.which("afplay"):
            candidate = sound_file if (sound_file and Path(sound_file).exists()) else "/System/Library/Sounds/Glass.aiff"
            os.spawnlp(os.P_NOWAIT, "afplay", "afplay", candidate)
            return
        # Linux
        for player, candidate in [
            ("paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"),
            ("aplay", "/usr/share/sounds/alsa/Front_Center.wav"),
        ]:
            if shutil.which(player) and Path(candidate).exists():
                os.spawnlp(os.P_NOWAIT, player, player, candidate)
                return
        # Fallback: terminal bell (may not be audible in GUI)
        print("\a", end="", flush=True)

    # ----------------------------- Helpers -----------------------------
    def set_status(self, text: str):
        self.var_status.set(text)

# ----------------------------- Main -----------------------------

def main():
    ap = argparse.ArgumentParser(description="PharmApp Reminder Config GUI (Tkinter)")
    ap.add_argument("--config", "-c", default="reminders.toml", help="Path to reminders.toml (default: reminders.toml)")
    args = ap.parse_args()

    path = Path(args.config).resolve()
    app = ReminderConfigApp(config_path=path if path.exists() else None)
    if not path.exists():
        # Store the intended path in the UI so Save goes there by default
        app.var_path.set(str(path))
        app.config_path = path
    app.mainloop()

if __name__ == "__main__":
    main()
