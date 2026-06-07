from __future__ import annotations

import os
import subprocess
from collections.abc import Callable

DEFAULT_DEV_VERSION = "0.0.0-dev"


def normalize_release_version(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("release version cannot be empty")
    if value.startswith(("v", "V")):
        return value[1:]
    return value


def current_git_tag() -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    tag = result.stdout.strip()
    return tag or None


def resolve_release_version(
    env: dict[str, str] | None = None,
    tag_lookup: Callable[[], str | None] | None = None,
    default: str = DEFAULT_DEV_VERSION,
) -> str:
    values = env if env is not None else os.environ

    for key in ("SLEEP_COACH_VERSION", "GITHUB_REF_NAME"):
        raw = values.get(key, "").strip()
        if raw:
            return normalize_release_version(raw)

    lookup = tag_lookup if tag_lookup is not None else current_git_tag
    tag = lookup()
    if tag:
        return normalize_release_version(tag)

    return default


def main() -> None:
    print(resolve_release_version())


if __name__ == "__main__":
    main()
