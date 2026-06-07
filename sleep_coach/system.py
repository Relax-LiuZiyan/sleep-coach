from __future__ import annotations

import os
import subprocess
from pathlib import Path


def configure_launch_on_startup(enabled: bool, project_root: Path) -> None:
    startup_dir = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    launcher = startup_dir / "sleep-coach.cmd"
    pythonw = Path(os.sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.exists() else Path(os.sys.executable)
    command = f'@echo off\r\ncd /d "{project_root}"\r\nstart "" "{interpreter}" "{project_root / "run.py"}"\r\n'

    if enabled:
        launcher.write_text(command, encoding="utf-8")
    elif launcher.exists():
        launcher.unlink()


def perform_shutdown() -> None:
    suppress_real_shutdown = os.environ.get("SLEEP_COACH_SUPPRESS_SHUTDOWN") == "1"
    if suppress_real_shutdown:
        print("[sleep-coach] Real shutdown suppressed. Unset SLEEP_COACH_SUPPRESS_SHUTDOWN to enable.")
        return
    subprocess.Popen(["shutdown", "/s", "/t", "0"])
