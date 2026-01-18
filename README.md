# PharmApp Reminder Config & Runner

A lightweight, cross-platform reminder toolkit built with the Python standard library:

- **`remind_config_gui.py`**: a PharmApp-themed **Tkinter GUI** to create and edit a `reminders.toml` file.
- **`remind_runner.py`**: a **hot-reloading runner** that reads `reminders.toml` and triggers reminders (and optional commands) at scheduled times.

This repository is designed to be simple, dependency-free, and easy to run on Windows, macOS, and Linux.

---

## Features

### 1) Reminder Config GUI (Tkinter)
- Edit **timezone**, **global sound file**, and **task list**
- Task fields: `time`, `type` (`notify` / `command` / `both`), `message`, `command`, `days`, `enabled`, `sound`
- Quick day presets: **Every day**, **Weekdays**, **Weekend**, **Clear**
- Task management: **Add / Duplicate / Delete / Reorder**
- Built-in sound test and pickers for sound files and commands/scripts
- Keyboard shortcuts:
  - **Ctrl+O** Open
  - **Ctrl+S** Save
  - **Ctrl+Shift+S** Save As
  - **F2** Add task
  - **Ctrl+D** Duplicate task
  - **Delete** Remove task
  - **Alt+Up / Alt+Down** Reorder

### 2) Reminder Runner (CLI)
- Reads `reminders.toml` and runs continuously
- **Hot reload**: automatically reloads config when the TOML file changes
- Day filters: supports **Mon–Sun** and also Vietnamese shorthand **T2–CN**
- Optional sound on trigger (platform-specific fallbacks)
- Optional command execution (for automation)

---

## Requirements

- **Python 3.11+** (uses `tomllib` from the standard library)

No external packages are required.

---

## Quick Start

### 1) Clone and enter the project
```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_FOLDER>
```

### 2) Create a config file: `reminders.toml`
Create a file next to the scripts named `reminders.toml` (or choose your own name).

Example:

```toml
timezone = "Asia/Ho_Chi_Minh"
sound_file = "C:/Windows/Media/notify.wav"

[[task]]
time = "07:30"
type = "both"
message = "Run morning script"
command = "python C:/path/to/script.py"
days = ["Mon","Tue","Wed","Thu","Fri"]
enabled = true
sound = true

[[task]]
time = "15:00"
type = "notify"
message = "Daily report"
enabled = true
sound = true
```

Notes:
- If `days` is omitted or empty, the task runs **every day**.
- `time` must be **24-hour `HH:MM`**.
- `type` controls behavior:
  - `notify`: print a reminder message
  - `command`: run the command only
  - `both`: notify + run command

---

## Usage

### Option A — Use the GUI to edit the TOML
```bash
python remind_config_gui.py --config reminders.toml
```

### Option B — Run the reminder runner
```bash
python remind_runner.py --config reminders.toml
```

Optional polling interval (seconds):
```bash
python remind_runner.py --config reminders.toml --tick 5
```

---

## TOML Schema Reference

Top-level keys:

```toml
timezone = "Asia/Ho_Chi_Minh"
sound_file = "/path/to/sound.wav"   # optional
```

Each task block:

```toml
[[task]]
time = "08:00"                      # required
type = "notify"                     # notify | command | both
message = "Reminder"                # shown in console output
command = "python /path/to/job.py"  # optional
days = ["Mon","Tue"]                # optional (Mon..Sun or T2..CN)
enabled = true                      # optional (default true)
sound = true                        # optional (default true)
```

Day values supported by the runner:
- English: `Mon Tue Wed Thu Fri Sat Sun`
- Vietnamese shorthand: `T2 T3 T4 T5 T6 T7 CN`

---

## Platform Notes

### Sound playback
- **Windows**: uses `winsound` (best with `.wav`). If no sound file exists, it uses a default system beep.
- **macOS**: uses `afplay` when available (plays common formats).
- **Linux**: tries `paplay` or `aplay` with common system sound locations.
- If no audio backend is available, it falls back to a terminal bell.

### Command execution
The runner starts commands using:
- `subprocess.Popen(cmd, shell=True)`

Recommendations:
- Prefer absolute paths.
- Quote paths with spaces.
- Do not run untrusted TOML configs.

---

## Troubleshooting

- **Nothing triggers**: ensure the runner is running continuously and your system clock/timezone is correct.
- **Invalid time format**: the `time` must be `HH:MM` (24-hour).
- **Sound doesn’t play**:
  - Verify the `sound_file` path exists.
  - On Windows, prefer `.wav`.
- **Days not matching**: check the `days` list (Mon–Sun or T2–CN).

---

## Project Layout

```
.
├─ remind_config_gui.py   # Tkinter GUI to edit reminders.toml
├─ remind_runner.py       # Runner that triggers reminders + optional commands
└─ reminders.toml         # Your configuration (create this)
```

---

## License

Add your preferred license (MIT/Apache-2.0/GPL-3.0, etc.) to the repository.
