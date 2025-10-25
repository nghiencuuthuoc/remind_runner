
# remind_runner.py
# Cross-platform reminder runner with hot-reloading TOML config and sound on trigger.
# Usage:
#   python remind_runner.py --config reminders.toml
#
# Example TOML is provided in the separate 'reminders.toml' file placed next to this script.

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple

try:
    import tomllib  # Python 3.11+
except Exception:
    print("ERROR: Python 3.11+ is required (needs tomllib).")
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    print("ERROR: Python 3.9+ is required (needs zoneinfo).")
    sys.exit(1)

DAYS_MAP = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6,
    "T2": 0, "T3": 1, "T4": 2, "T5": 3, "T6": 4, "T7": 5, "CN": 6,
}

@dataclass
class Task:
    time: str
    type: str = "notify"
    message: str = "Reminder"
    command: Optional[str] = None
    days: Optional[List[str]] = None
    enabled: bool = True
    sound: bool = True
    id_key: str = field(init=False)

    def __post_init__(self):
        core = f"{self.time}|{self.type}|{self.message}|{self.command or ''}"
        self.id_key = core

@dataclass
class Config:
    timezone: str = "Asia/Ho_Chi_Minh"
    tasks: List[Task] = field(default_factory=list)
    sound_file: Optional[str] = None

def load_config(path: Path) -> Config:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    timezone = data.get("timezone", "Asia/Ho_Chi_Minh")
    sound_file = data.get("sound_file", None)
    raw_tasks = data.get("task", []) or data.get("tasks", [])
    tasks: List[Task] = []
    for t in raw_tasks:
        tasks.append(Task(
            time=t["time"],
            type=t.get("type", "notify"),
            message=t.get("message", "Reminder"),
            command=t.get("command"),
            days=t.get("days"),
            enabled=t.get("enabled", True),
            sound=t.get("sound", True),
        ))
    return Config(timezone=timezone, tasks=tasks, sound_file=sound_file)

def parse_hhmm(hhmm: str) -> Tuple[int, int]:
    try:
        hh, mm = hhmm.split(":")
        return int(hh), int(mm)
    except Exception:
        raise ValueError(f"Invalid time format '{hhmm}'. Use 'HH:MM' 24h.")

def today_str(now: dt.datetime) -> str:
    return now.strftime("%Y-%m-%d")

def in_daylist(now: dt.datetime, days: Optional[List[str]]) -> bool:
    if not days:
        return True
    day_idx = now.weekday()
    allowed = set()
    for d in days:
        if d in DAYS_MAP:
            allowed.add(DAYS_MAP[d])
    return day_idx in allowed if allowed else True

def play_sound(sound_file: Optional[str] = None):
    # 1) Windows
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
    # 2) macOS
    if shutil.which("afplay"):
        candidate = sound_file if (sound_file and Path(sound_file).exists()) else "/System/Library/Sounds/Glass.aiff"
        subprocess.Popen(["afplay", candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    # 3) Linux
    for player, candidate in [
        ("paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"),
        ("aplay", "/usr/share/sounds/alsa/Front_Center.wav"),
    ]:
        if shutil.which(player) and Path(candidate).exists():
            subprocess.Popen([player, candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    # 4) Fallback
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass

def run_command(cmd: str):
    try:
        print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching command: {cmd}")
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"ERROR running command '{cmd}': {e}")

def main():
    ap = argparse.ArgumentParser(description="Simple reminder runner with hot-reloading TOML config.")
    ap.add_argument("--config", "-c", default="reminders.toml", help="Path to TOML config (default: reminders.toml)")
    ap.add_argument("--tick", type=int, default=5, help="Polling interval in seconds (default: 5)")
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Create it based on the provided 'reminders.toml' example.")
        sys.exit(1)

    last_mtime = None
    cfg: Optional[Config] = None
    last_run: Dict[str, str] = {}

    tz: ZoneInfo = ZoneInfo("Asia/Ho_Chi_Minh")

    while True:
        try:
            mtime = config_path.stat().st_mtime
            if (cfg is None) or (last_mtime is None) or (mtime != last_mtime):
                cfg = load_config(config_path)
                tz = ZoneInfo(cfg.timezone)
                print(f"[Reloaded config] timezone={cfg.timezone}, tasks={len(cfg.tasks)}")
                last_mtime = mtime

            now = dt.datetime.now(tz)

            for t in cfg.tasks:
                if not t.enabled:
                    continue
                if not in_daylist(now, t.days):
                    continue
                try:
                    h, m = parse_hhmm(t.time)
                except ValueError as ve:
                    print(f"Config error in task '{t.message}': {ve}")
                    continue

                if now.hour == h and now.minute == m:
                    today = today_str(now)
                    if last_run.get(t.id_key) != today:
                        last_run[t.id_key] = today
                        stamp = now.strftime("%Y-%m-%d %H:%M")
                        print(f"[{stamp}] 🔔 {t.message}")
                        if t.sound:
                            play_sound(cfg.sound_file)
                        if t.type in ("command", "both") and t.command:
                            run_command(t.command)

            time.sleep(max(1, int(args.tick)))
        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"[Loop error] {e}")
            time.sleep(max(1, int(args.tick)))

if __name__ == "__main__":
    main()
