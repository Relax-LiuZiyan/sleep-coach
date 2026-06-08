from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from sleep_coach.app import main


def _show_fatal_error(message: str) -> None:
    app = QApplication.instance() or QApplication([])
    QMessageBox.critical(None, "Sleep Coach", message)


def _write_error_log(message: str) -> None:
    root = Path.home() / ".sleep-coach"
    root.mkdir(parents=True, exist_ok=True)
    (root / "launcher-error.log").write_text(message, encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except SystemExit:
        raise
    except Exception:
        details = traceback.format_exc()
        _write_error_log(details)
        _show_fatal_error(
            "Sleep Coach 启动失败，错误日志已写入：\n"
            f"{Path.home() / '.sleep-coach' / 'launcher-error.log'}"
        )
