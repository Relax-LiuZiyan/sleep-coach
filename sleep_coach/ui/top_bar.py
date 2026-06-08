from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ..models import Snapshot
from ..schedule import LATE_NIGHT_WRAP_HOUR, parse_clock, to_clock_minutes

DAYTIME_TOP_BAR_COPY = "白天先稳住，晚上按计划收尾。"
PRE_SLEEP_TOP_BAR_COPY = "开始收心，别把今晚又拖烂。"
PRE_SLEEP_WINDOW_MINUTES = 150
ATTENTION_STAGES = {"warning", "overtime", "fullscreen", "penalty"}


class TopBarWindow(QWidget):
    open_settings_requested = Signal()
    position_changed = Signal(int, int)

    def __init__(self, x: int | None, y: int | None, always_on_top: bool) -> None:
        self._always_on_top = always_on_top
        super().__init__(None, self._flags_for(always_on_top))
        self.setObjectName("topBarRoot")
        self.setWindowTitle("Sleep Coach Top Bar")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QGuiApplication.primaryScreen()
        available_width = screen.availableGeometry().width() if screen is not None else 1920
        self._bar_width = min(1560, max(1240, available_width - 80))
        self.setFixedSize(self._bar_width, 86)

        self._drag_offset: QPoint | None = None
        self._quote_text = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 12, 30, 12)
        layout.setSpacing(34)

        self.time_label = QLabel("REM 00:00:00")
        self.time_label.setObjectName("topBarTime")
        self.now_label = QLabel("NOW 00:00:00")
        self.now_label.setObjectName("topBarClock")
        self.quote_label = QLabel("收得住今晚，明天才稳得住。")
        self.quote_label.setObjectName("topBarQuote")
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.quote_label.setMinimumWidth(0)

        layout.addWidget(self.time_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.now_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.quote_label, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        default_x = max(20, (available_width - self._bar_width) // 2)
        self.move(x if x is not None else default_x, y if y is not None else 16)

    def _flags_for(self, always_on_top: bool):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        return flags

    def _refresh_quote_text(self) -> None:
        max_width = max(220, self.quote_label.width() - 6)
        font = QFont(self.quote_label.font())
        base_size = font.pointSizeF() if font.pointSizeF() > 0 else 24.0
        font.setPointSizeF(base_size)

        while font.pointSizeF() > 15.0:
            metrics = QFontMetrics(font)
            if metrics.horizontalAdvance(self._quote_text) <= max_width:
                break
            font.setPointSizeF(font.pointSizeF() - 0.5)

        self.quote_label.setFont(font)
        metrics = QFontMetrics(font)
        if metrics.horizontalAdvance(self._quote_text) <= max_width:
            self.quote_label.setText(self._quote_text)
        else:
            self.quote_label.setText(metrics.elidedText(self._quote_text, Qt.TextElideMode.ElideRight, max_width))

    def _current_minutes(self, now_label: str) -> int:
        hours_text, minutes_text, _seconds_text = now_label.split(":")
        hours = int(hours_text)
        minutes = int(minutes_text)
        total = hours * 60 + minutes
        return total + 1440 if hours < LATE_NIGHT_WRAP_HOUR else total

    def _top_bar_copy(self, snapshot: Snapshot) -> str:
        if snapshot.stage != "idle":
            return " ".join(snapshot.quote.split())

        warning_time = (
            snapshot.today_weekend_warning_time
            if snapshot.is_weekend
            else snapshot.today_weekday_warning_time
        )
        warning_hours, warning_minutes = parse_clock(warning_time)
        warning_total = to_clock_minutes(f"{warning_hours:02d}:{warning_minutes:02d}")
        current_total = self._current_minutes(snapshot.now_label)
        minutes_until_warning = max(0, warning_total - current_total)

        if minutes_until_warning <= PRE_SLEEP_WINDOW_MINUTES:
            return PRE_SLEEP_TOP_BAR_COPY
        return DAYTIME_TOP_BAR_COPY

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_offset:
            self._drag_offset = None
            self.position_changed.emit(self.x(), self.y())

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_settings_requested.emit()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._refresh_quote_text()

    def update_snapshot(self, snapshot: Snapshot) -> None:
        self.time_label.setText(f"REM {snapshot.remaining_label}")
        self.now_label.setText(f"NOW {snapshot.now_label}")
        self._quote_text = self._top_bar_copy(snapshot)
        self._refresh_quote_text()

        if snapshot.stage == "idle":
            self.setStyleSheet(
                "#topBarRoot { background: rgba(15, 18, 30, 220); "
                "border: 1px solid rgba(255,255,255,24); border-radius: 24px; }"
            )
        elif snapshot.stage in {"warning", "overtime"}:
            self.setStyleSheet(
                "#topBarRoot { background: rgba(87, 54, 11, 228); "
                "border: 1px solid rgba(255,205,126,56); border-radius: 24px; }"
            )
        else:
            self.setStyleSheet(
                "#topBarRoot { background: rgba(94, 18, 18, 230); "
                "border: 1px solid rgba(255,140,140,62); border-radius: 24px; }"
            )

    def apply_settings(self, snapshot: Snapshot) -> None:
        force_on_top = snapshot.settings.top_bar_always_on_top or snapshot.stage in ATTENTION_STAGES
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, force_on_top)
        self.show()
