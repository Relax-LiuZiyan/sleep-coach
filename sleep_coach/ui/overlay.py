from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..models import Snapshot


class OverlayWindow(QWidget):
    sleep_now_requested = Signal()
    cancel_requested = Signal()
    overtime_requested = Signal()

    def __init__(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        super().__init__(None, flags)
        self.setObjectName("overlayRoot")
        self.setWindowTitle("Sleep Coach Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.addStretch(1)

        self.eyebrow = QLabel("最后一分钟")
        self.eyebrow.setObjectName("eyebrow")
        self.eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label = QLabel("1:00")
        self.timer_label.setObjectName("overlayTimer")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.quote_label = QLabel("现在停下来，明天才站得稳。")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setObjectName("overlayQuote")

        self.meta_label = QLabel("")
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meta_label.setObjectName("bodyCopy")

        self.action_row = QHBoxLayout()
        self.action_row.setSpacing(14)
        self.sleep_now_button = QPushButton("现在休息")
        self.cancel_button = QPushButton("取消并接受惩罚")
        self.cancel_button.setProperty("variant", "ghost")
        self.overtime_button = QPushButton("申请临时加班")
        self.overtime_button.setProperty("variant", "ghost")
        self.action_row.addStretch(1)
        self.action_row.addWidget(self.sleep_now_button)
        self.action_row.addWidget(self.cancel_button)
        self.action_row.addWidget(self.overtime_button)
        self.action_row.addStretch(1)

        layout.addWidget(self.eyebrow)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.quote_label)
        layout.addSpacing(10)
        layout.addWidget(self.meta_label)
        layout.addSpacing(28)
        layout.addLayout(self.action_row)
        layout.addStretch(1)

        self.sleep_now_button.clicked.connect(self.sleep_now_requested.emit)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        self.overtime_button.clicked.connect(self.overtime_requested.emit)

    def update_snapshot(self, snapshot: Snapshot) -> None:
        if snapshot.stage == "penalty":
            self.eyebrow.setText("取消成本")
            self.timer_label.setText(snapshot.penalty_countdown_label)
            self.meta_label.setText("这不是继续努力，这是拿明天的状态给今天的拖延补票。")
            self.sleep_now_button.hide()
            self.cancel_button.hide()
            self.overtime_button.hide()
        else:
            self.eyebrow.setText("现在收尾")
            self.timer_label.setText(snapshot.fullscreen_countdown_label)
            self.meta_label.setText(
                f"连续完成 {snapshot.streak} 天，本周临时加班 {snapshot.weekly_overtime_used}/{snapshot.weekly_overtime_limit}"
            )
            self.sleep_now_button.show()
            self.cancel_button.show()
            self.overtime_button.show()

        self.quote_label.setText(snapshot.quote)
