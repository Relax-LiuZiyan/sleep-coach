from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QStyle, QSystemTrayIcon, QWidget

from .controller import SleepCoachController
from .runtime import app_icon_path, launch_working_directory
from .ui.main_window import MainWindow
from .ui.overlay import OverlayWindow
from .ui.styles import build_app_style
from .ui.top_bar import TopBarWindow

ATTENTION_STAGES = {"warning", "overtime", "fullscreen", "penalty"}


def app_root():
    return Path.home() / ".sleep-coach"


def should_show_main_window(argv: list[str] | None = None) -> bool:
    args = argv if argv is not None else sys.argv
    return "--show" in args


def handle_overlay_sleep_now(controller: SleepCoachController) -> None:
    controller.sleep_now(trigger_shutdown=True)


def handle_tray_sleep_now(
    controller: SleepCoachController,
    *,
    confirm_shutdown,
) -> None:
    if not confirm_shutdown():
        return
    controller.sleep_now(trigger_shutdown=True)


def handle_tray_exit(
    main_window: MainWindow,
    app: QApplication,
    tray: QSystemTrayIcon,
    *,
    extra_windows: list[QWidget] | None = None,
) -> None:
    main_window.prepare_to_quit()
    main_window.close()
    for window in extra_windows or []:
        window.close()
    tray.hide()
    app.exit(0)


def build_tray(
    app: QApplication,
    controller: SleepCoachController,
    main_window: MainWindow,
    *,
    extra_windows: list[QWidget] | None = None,
) -> QSystemTrayIcon:
    def confirm_shutdown() -> bool:
        result = QMessageBox.question(
            main_window,
            "立刻休息",
            "确认现在立刻休息并马上关机吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    icon = QIcon(str(app_icon_path()))
    tray = QSystemTrayIcon(icon if not icon.isNull() else app.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarShadeButton), app)
    tray.setToolTip("Sleep Coach")
    menu = QMenu()
    open_action = QAction("打开主界面", tray)
    open_action.triggered.connect(main_window.showNormal)
    open_action.triggered.connect(main_window.raise_)
    open_action.triggered.connect(main_window.activateWindow)
    sleep_action = QAction("立刻休息", tray)
    sleep_action.triggered.connect(
        lambda: handle_tray_sleep_now(controller, confirm_shutdown=confirm_shutdown)
    )
    quit_action = QAction("退出", tray)
    quit_action.triggered.connect(
        lambda: handle_tray_exit(main_window, app, tray, extra_windows=extra_windows)
    )
    menu.addAction(open_action)
    menu.addAction(sleep_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: (main_window.showNormal(), main_window.raise_(), main_window.activateWindow())
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()
    return tray


def main(argv: list[str] | None = None) -> int:
    launch_args = argv if argv is not None else sys.argv
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(launch_args)
    app.setApplicationName("Sleep Coach")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(build_app_style(1.0))
    icon = QIcon(str(app_icon_path()))
    if not icon.isNull():
        app.setWindowIcon(icon)

    project_root = launch_working_directory()
    controller = SleepCoachController(app_root(), project_root)
    controller.tick()
    main_window = MainWindow(controller.snapshot)
    overlay = OverlayWindow()
    top_bar = TopBarWindow(
        controller.settings.top_bar_x,
        controller.settings.top_bar_y,
        controller.settings.top_bar_always_on_top,
    )
    if not icon.isNull():
        main_window.setWindowIcon(icon)
        overlay.setWindowIcon(icon)
        top_bar.setWindowIcon(icon)
    tray = build_tray(app, controller, main_window, extra_windows=[top_bar, overlay])
    show_main_window = should_show_main_window(launch_args)
    last_attention_stage: dict[str, str | None] = {"value": None}

    def apply_snapshot(snapshot) -> None:
        main_window.update_snapshot(snapshot)
        top_bar.update_snapshot(snapshot)
        top_bar.apply_settings(snapshot)
        overlay.update_snapshot(snapshot)
        previous_stage = last_attention_stage["value"]
        current_stage = snapshot.stage

        if current_stage in ATTENTION_STAGES and current_stage != previous_stage:
            top_bar.show()
            top_bar.raise_()
            top_bar.activateWindow()

        if snapshot.stage in {"fullscreen", "penalty"}:
            screen = app.primaryScreen()
            if screen:
                overlay.setGeometry(screen.availableGeometry())
            overlay.showFullScreen()
            overlay.raise_()
            overlay.activateWindow()
        else:
            overlay.hide()

        last_attention_stage["value"] = current_stage

    def request_overtime() -> None:
        ok, message = controller.request_overtime()
        if ok:
            main_window.show_info(message)
        else:
            main_window.show_error(message)

    controller.snapshot_changed.connect(apply_snapshot)
    controller.error_raised.connect(main_window.show_error)
    main_window.settings_saved.connect(controller.save_settings)
    main_window.overtime_requested.connect(request_overtime)
    main_window.favorite_toggled.connect(controller.set_favorite)
    top_bar.open_settings_requested.connect(
        lambda: (main_window.showNormal(), main_window.raise_(), main_window.activateWindow())
    )
    top_bar.position_changed.connect(controller.update_top_bar_position)
    overlay.sleep_now_requested.connect(lambda: handle_overlay_sleep_now(controller))
    overlay.cancel_requested.connect(controller.cancel_shutdown)
    overlay.overtime_requested.connect(request_overtime)

    controller.start()
    apply_snapshot(controller.snapshot)
    if show_main_window:
        main_window.show()
    top_bar.show()

    exit_code = app.exec()
    tray.hide()
    return exit_code
