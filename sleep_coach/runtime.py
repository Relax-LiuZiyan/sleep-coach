from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def source_root() -> Path:
    return Path(__file__).resolve().parent.parent


def bundle_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(sys.executable).resolve().parent


def resource_root() -> Path:
    if is_frozen():
        return bundle_root()
    return source_root()


def app_icon_path() -> Path:
    return resource_root() / "sleep_coach" / "assets" / "sleep_coach.ico"


def launch_working_directory() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return source_root()
