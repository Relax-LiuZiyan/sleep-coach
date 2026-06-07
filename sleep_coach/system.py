from __future__ import annotations

import os
import subprocess
from pathlib import Path


def build_startup_command(
    *,
    executable_path: Path,
    working_directory: Path,
    frozen: bool,
) -> str:
    if frozen:
        return f'@echo off\r\ncd /d "{working_directory}"\r\nstart "" "{executable_path}"\r\n'

    pythonw = executable_path.with_name("pythonw.exe")
    interpreter = pythonw if executable_path.name.lower() == "python.exe" else executable_path
    return f'@echo off\r\ncd /d "{working_directory}"\r\nstart "" "{interpreter}" "{working_directory / "run.py"}"\r\n'


def configure_launch_on_startup(enabled: bool, project_root: Path) -> None:
    startup_dir = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    launcher = startup_dir / "sleep-coach.cmd"
    command = build_startup_command(
        executable_path=Path(os.sys.executable),
        working_directory=project_root,
        frozen=bool(getattr(os.sys, "frozen", False)),
    )

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
