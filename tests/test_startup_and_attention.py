from __future__ import annotations

import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from sleep_coach import app as app_module
from sleep_coach.models import Snapshot, default_settings
from sleep_coach.system import build_startup_command
from sleep_coach.ui.top_bar import TopBarWindow


class StartupAndAttentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def _snapshot(self, stage: str, *, always_on_top: bool = False) -> Snapshot:
        settings = default_settings()
        settings.top_bar_always_on_top = always_on_top
        return Snapshot(
            stage=stage,
            remaining_label="00:10:00",
            quote="测试文案",
            quote_id="q1",
            quote_is_favorite=False,
            now_label="12:00:00",
            is_weekend=False,
            streak=0,
            weekly_overtime_used=0,
            weekly_overtime_limit=2,
            fullscreen_countdown_label="1:00",
            penalty_countdown_label="0:45",
            planned_shutdown_time="23:15",
            today_weekday_warning_time="23:10",
            today_weekday_shutdown_time="23:15",
            today_weekend_warning_time="23:30",
            today_weekend_shutdown_time="00:00",
            record_stats=[],
            settings=settings,
        )

    def test_background_flag_hides_main_window_on_startup(self) -> None:
        self.assertFalse(app_module.should_show_main_window(["launch_sleep_coach.pyw", "--background"]))
        self.assertFalse(app_module.should_show_main_window(["launch_sleep_coach.pyw"]))
        self.assertTrue(app_module.should_show_main_window(["launch_sleep_coach.pyw", "--show"]))

    def test_startup_command_uses_background_flag(self) -> None:
        command = build_startup_command(
            executable_path=Path(r"C:\Python\python.exe"),
            working_directory=Path(r"D:\sleep"),
            frozen=False,
        )
        self.assertIn('launch_sleep_coach.pyw" --background', command)

    def test_top_bar_forces_on_top_during_warning_stage(self) -> None:
        bar = TopBarWindow(None, 16, False)
        try:
            bar.apply_settings(self._snapshot("warning", always_on_top=False))
            self.assertTrue(bool(bar.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        finally:
            bar.close()

    def test_top_bar_respects_setting_when_idle(self) -> None:
        bar = TopBarWindow(None, 16, False)
        try:
            bar.apply_settings(self._snapshot("idle", always_on_top=False))
            self.assertFalse(bool(bar.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        finally:
            bar.close()


if __name__ == "__main__":
    unittest.main()
