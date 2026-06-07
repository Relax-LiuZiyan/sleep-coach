from __future__ import annotations

from PySide6.QtCore import QEvent, QTime, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import Settings, Snapshot
from .styles import build_app_style

DESIGN_WIDTH = 1360
DESIGN_HEIGHT = 900

EDIT_GATE_QUOTES = [
    "今天的你一松手，就像那天她放弃你一样干脆。你对自己，也不过如此。",
    "你不是在改时间，你是在给今晚的失控找一张看起来体面的通行证。",
    "再晚一点没有浪漫，只有明天那个发飘、出汗、没劲、看谁都烦的你。",
    "你以为只是放宽十几分钟，实际上是在把明天的状态一刀一刀往下削。",
    "连睡觉这件事都守不住，你还指望自己在更大的事上突然争气？",
]


def card() -> QFrame:
    frame = QFrame()
    frame.setProperty("card", True)
    return frame


def subtle_panel() -> QFrame:
    frame = QFrame()
    frame.setProperty("subtlePanel", True)
    return frame


class TimeEditGateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("修改时间")
        self.setModal(True)
        self.setFixedSize(760, 470)
        self._seconds_left = 30
        self._quote_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        eyebrow = QLabel("修改时间前先停 30 秒")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("先看完，再决定要不要放宽规则")
        title.setObjectName("gateTitle")
        title.setWordWrap(True)

        self.countdown_label = QLabel("30 s")
        self.countdown_label.setObjectName("gateTimer")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.quote_label = QLabel(EDIT_GATE_QUOTES[0])
        self.quote_label.setObjectName("gateQuote")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tip = QLabel("倒计时结束前不能修改。看完这 30 秒，再决定是不是值得把明天一起拖下水。")
        tip.setObjectName("bodyCopy")
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_row = QHBoxLayout()
        button_row.setSpacing(14)
        self.cancel_button = QPushButton("先不改了")
        self.cancel_button.setProperty("variant", "ghost")
        self.unlock_button = QPushButton("还要看 30 s")
        self.unlock_button.setEnabled(False)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)
        self.unlock_button.setAutoDefault(False)
        self.unlock_button.setDefault(False)
        button_row.addWidget(self.cancel_button)
        button_row.addStretch(1)
        button_row.addWidget(self.unlock_button)

        root.addWidget(eyebrow)
        root.addWidget(title)
        root.addStretch(1)
        root.addWidget(self.countdown_label)
        root.addWidget(self.quote_label)
        root.addWidget(tip)
        root.addStretch(1)
        root.addLayout(button_row)

        self.cancel_button.clicked.connect(self.reject)
        self.unlock_button.clicked.connect(self.accept)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        self._seconds_left -= 1
        self.countdown_label.setText(f"{max(0, self._seconds_left)} s")

        if self._seconds_left in {24, 18, 12, 6}:
            self._quote_index = (self._quote_index + 1) % len(EDIT_GATE_QUOTES)
            self.quote_label.setText(EDIT_GATE_QUOTES[self._quote_index])

        if self._seconds_left > 0:
            self.unlock_button.setText(f"还要看 {self._seconds_left} s")
            return

        self._timer.stop()
        self.unlock_button.setEnabled(True)
        self.unlock_button.setText("进入修改")


class MainWindow(QMainWindow):
    settings_saved = Signal(object)
    overtime_requested = Signal()
    favorite_toggled = Signal(str, bool)

    def __init__(self, initial: Snapshot) -> None:
        super().__init__()
        self._latest_snapshot = initial
        self._allow_close = False
        self._schedule_unlocked = False
        self._strategy_unlocked = False
        self._schedule_dirty = False
        self._settings_dirty = False
        self._syncing_form = False
        self._scaled_heights: list[tuple[QWidget, int]] = []
        self._scaled_widths: list[tuple[QWidget, int]] = []
        self.record_cells: dict[str, QLabel] = {}

        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowTitle("Sleep Coach")
        self.resize(1480, 1040)
        self.setMinimumSize(1460, 1000)

        dashboard = QWidget()
        dashboard.setObjectName("mainSurface")
        root = QVBoxLayout(dashboard)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(18)

        hero_row = QHBoxLayout()
        hero_row.setSpacing(18)

        hero_left = card()
        hero_left_layout = QVBoxLayout(hero_left)
        hero_left_layout.setContentsMargins(24, 24, 24, 24)
        hero_left_layout.setSpacing(12)

        eyebrow = QLabel("SLEEP COACH")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("今晚按时下线")
        title.setObjectName("titleHero")
        copy = QLabel("工作日默认 23:10 开始收尾，23:15 进入强提醒。今晚早点停，明天身体和状态才稳。")
        copy.setWordWrap(True)
        copy.setObjectName("bodyCopy")

        chips_row = QHBoxLayout()
        chips_row.setSpacing(14)
        stage_chip, self.stage_value = self._metric_chip("阶段", "--")
        remaining_chip, self.remaining_value = self._metric_chip("REM", "00:00:00")
        now_chip, self.now_value = self._metric_chip("NOW", "00:00:00")
        chips_row.addWidget(stage_chip)
        chips_row.addWidget(remaining_chip)
        chips_row.addWidget(now_chip)

        hero_left_layout.addWidget(eyebrow)
        hero_left_layout.addWidget(title)
        hero_left_layout.addWidget(copy)
        hero_left_layout.addLayout(chips_row)
        hero_left_layout.addStretch(1)

        hero_right = card()
        hero_right_layout = QVBoxLayout(hero_right)
        hero_right_layout.setContentsMargins(24, 24, 24, 24)
        hero_right_layout.setSpacing(12)

        quote_label = QLabel("今日狠话")
        quote_label.setObjectName("eyebrow")
        self.quote_text = QLabel(initial.quote)
        self.quote_text.setWordWrap(True)
        self.quote_text.setObjectName("quoteHero")
        quote_hint = QLabel("收藏后，这句会比普通文案更常出现。")
        quote_hint.setObjectName("bodyCopy")
        self.favorite_button = QPushButton("收藏这句")
        self.favorite_button.clicked.connect(self._toggle_favorite)

        hero_right_layout.addWidget(quote_label)
        hero_right_layout.addWidget(self.quote_text, 1)
        hero_right_layout.addWidget(quote_hint)
        hero_right_layout.addWidget(self.favorite_button, alignment=Qt.AlignmentFlag.AlignLeft)

        hero_row.addWidget(hero_left, 3)
        hero_row.addWidget(hero_right, 2)
        root.addLayout(hero_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.streak_value = self._stat_card("连续完成", "0")
        self.overtime_value = self._stat_card("本周加班", "0/0")
        self.shutdown_value = self._stat_card("今晚关机", "--:--")
        stats_row.addWidget(self.streak_value[0])
        stats_row.addWidget(self.overtime_value[0])
        stats_row.addWidget(self.shutdown_value[0])
        root.addLayout(stats_row)

        lower_row = QHBoxLayout()
        lower_row.setSpacing(18)

        self.weekday_warning = QTimeEdit()
        self.weekday_shutdown = QTimeEdit()
        self.weekend_warning = QTimeEdit()
        self.weekend_shutdown = QTimeEdit()
        self.fullscreen_seconds = QSpinBox()
        self.penalty_seconds = QSpinBox()
        self.overtime_minutes = QSpinBox()
        self.weekly_limit = QSpinBox()
        self.launch_on_startup = QCheckBox("开机自动运行")
        self.top_bar_on_top = QCheckBox("顶部条始终置顶")
        self.save_button = QPushButton("保存设置")
        self.overtime_button = QPushButton("申请临时加班")
        self.control_note = QLabel("")
        self.schedule_note = QLabel("")
        self.unlock_schedule_button = QPushButton("修改时间")
        self.unlock_strategy_button = QPushButton("解锁参数")

        for button in (
            self.favorite_button,
            self.save_button,
            self.overtime_button,
            self.unlock_schedule_button,
            self.unlock_strategy_button,
        ):
            button.setAutoDefault(False)
            button.setDefault(False)

        self._register_scaled_height(self.overtime_button, 42)
        self._register_scaled_height(self.save_button, 42)
        self._register_scaled_height(self.unlock_strategy_button, 42)
        self._register_scaled_width(self.overtime_button, 208)
        self._register_scaled_width(self.save_button, 172)
        self._register_scaled_width(self.unlock_strategy_button, 176)

        self.schedule_card = card()
        self._build_schedule_card(self.schedule_card)
        self.control_card = card()
        self._build_control_card(self.control_card)

        lower_row.addWidget(self.schedule_card, 1)
        lower_row.addWidget(self.control_card, 1)
        root.addLayout(lower_row, 1)

        self.setCentralWidget(dashboard)
        self._bind_dirty_tracking()
        self._set_schedule_editable(False)
        self._set_strategy_editable(False)
        self._apply_snapshot(initial)
        self._apply_scale()

    def _metric_chip(self, label_text: str, value_text: str) -> tuple[QFrame, QLabel]:
        frame = subtle_panel()
        frame.setProperty("metricChip", True)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("chipLabel")
        value = QLabel(value_text)
        value.setObjectName("chipValue")

        layout.addWidget(label)
        layout.addWidget(value)
        return frame, value

    def _stat_card(self, label_text: str, value_text: str) -> tuple[QFrame, QLabel]:
        frame = card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        value = QLabel(value_text)
        value.setObjectName("statValue")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(label_text)
        label.setObjectName("statLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)
        layout.addWidget(value)
        layout.addWidget(label)
        layout.addStretch(1)
        self._register_scaled_height(frame, 108)
        return frame, value

    def _configure_time_edit(self, widget: QTimeEdit) -> None:
        widget.setDisplayFormat("HH:mm")
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        widget.setKeyboardTracking(False)
        self._register_scaled_height(widget, 54)

    def _configure_spin(self, widget: QSpinBox, minimum: int, maximum: int, suffix: str) -> None:
        widget.setRange(minimum, maximum)
        widget.setSuffix(suffix)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self._register_scaled_height(widget, 38)

    def _bind_dirty_tracking(self) -> None:
        for widget in (
            self.weekday_warning,
            self.weekday_shutdown,
            self.weekend_warning,
            self.weekend_shutdown,
        ):
            widget.timeChanged.connect(self._mark_schedule_dirty)

        for widget in (
            self.fullscreen_seconds,
            self.penalty_seconds,
            self.overtime_minutes,
            self.weekly_limit,
        ):
            widget.valueChanged.connect(self._mark_settings_dirty)

        self.launch_on_startup.stateChanged.connect(self._mark_settings_dirty)
        self.top_bar_on_top.stateChanged.connect(self._mark_settings_dirty)

    def _mark_schedule_dirty(self, *_args) -> None:
        if not self._syncing_form and self._schedule_unlocked:
            self._schedule_dirty = True

    def _mark_settings_dirty(self, *_args) -> None:
        if not self._syncing_form:
            self._settings_dirty = True

    def _day_panel(self, title: str, hint: str, warning_widget: QTimeEdit, shutdown_widget: QTimeEdit) -> QFrame:
        self._configure_time_edit(warning_widget)
        self._configure_time_edit(shutdown_widget)

        frame = subtle_panel()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        panel_title = QLabel(title)
        panel_title.setObjectName("panelTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("helperText")

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        warning_label = QLabel("开始提醒")
        warning_label.setObjectName("fieldLabel")
        shutdown_label = QLabel("正式关机")
        shutdown_label.setObjectName("fieldLabel")
        form.addRow(warning_label, warning_widget)
        form.addRow(shutdown_label, shutdown_widget)

        layout.addWidget(panel_title)
        layout.addWidget(hint_label)
        layout.addLayout(form)
        return frame

    def _metric_edit_tile(self, label_text: str, widget: QSpinBox) -> QFrame:
        tile = subtle_panel()
        self._register_scaled_height(tile, 50)
        layout = QHBoxLayout(tile)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(10)

        label = QLabel(label_text)
        label.setObjectName("metricFieldLabel")
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._register_scaled_width(widget, 132)

        layout.addWidget(label, 1)
        layout.addWidget(widget)
        return tile

    def _build_record_table(self) -> QFrame:
        frame = subtle_panel()
        self._register_scaled_height(frame, 110)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(0)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        for period in ["本周", "本月", "本年"]:
            period_card = subtle_panel()
            card_layout = QVBoxLayout(period_card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(4)

            period_label = QLabel(period)
            period_label.setObjectName("recordPeriod")
            period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(period_label)

            on_time_row = QHBoxLayout()
            on_time_row.setSpacing(8)
            on_time_label = QLabel("准时")
            on_time_label.setObjectName("recordMetricLabel")
            on_time_value = QLabel("--")
            on_time_value.setObjectName("recordValue")
            on_time_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.record_cells[f"{period}:on_time"] = on_time_value
            on_time_row.addWidget(on_time_label)
            on_time_row.addStretch(1)
            on_time_row.addWidget(on_time_value)
            card_layout.addLayout(on_time_row)

            late_row = QHBoxLayout()
            late_row.setSpacing(8)
            late_label = QLabel("晚睡")
            late_label.setObjectName("recordMetricLabel")
            late_value = QLabel("--")
            late_value.setObjectName("recordValue")
            late_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ratio_value = QLabel("--")
            ratio_value.setObjectName("recordRatio")
            ratio_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.record_cells[f"{period}:late"] = late_value
            self.record_cells[f"{period}:ratio"] = ratio_value

            late_row.addWidget(late_label)
            late_row.addWidget(late_value)
            late_row.addStretch(1)
            late_row.addWidget(ratio_value)
            card_layout.addLayout(late_row)

            cards_row.addWidget(period_card, 1)

        layout.addLayout(cards_row)
        return frame

    def _register_scaled_height(self, widget: QWidget, base_height: int) -> None:
        self._scaled_heights.append((widget, base_height))
        widget.setFixedHeight(base_height)

    def _register_scaled_width(self, widget: QWidget, base_width: int) -> None:
        self._scaled_widths.append((widget, base_width))
        widget.setFixedWidth(base_width)

    def _build_schedule_card(self, frame: QFrame) -> None:
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        eyebrow = QLabel("时间计划")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("工作日 / 周末")
        title.setObjectName("cardTitle")
        copy = QLabel("工作日默认 23:10 提醒、23:15 关机。周末允许稍晚，但最晚不能超过 00:00。")
        copy.setWordWrap(True)
        copy.setObjectName("bodyCopy")

        panels = QHBoxLayout()
        panels.setSpacing(14)
        panels.addWidget(self._day_panel("工作日", "默认更严格。", self.weekday_warning, self.weekday_shutdown))
        panels.addWidget(self._day_panel("周末", "红线仍是 00:00。", self.weekend_warning, self.weekend_shutdown))

        action_row = QHBoxLayout()
        action_row.setSpacing(14)
        self.unlock_schedule_button.setProperty("variant", "ghost")
        self.unlock_schedule_button.clicked.connect(self._request_schedule_unlock)
        self.schedule_note.setObjectName("helperTextStrong")
        self.schedule_note.setWordWrap(True)
        action_row.addWidget(self.unlock_schedule_button)
        action_row.addWidget(self.schedule_note, 1)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(copy)
        layout.addLayout(panels, 1)
        layout.addLayout(action_row)

    def _build_control_card(self, frame: QFrame) -> None:
        self._configure_spin(self.fullscreen_seconds, 15, 180, " s")
        self._configure_spin(self.penalty_seconds, 15, 180, " s")
        self._configure_spin(self.overtime_minutes, 15, 180, " min")
        self._configure_spin(self.weekly_limit, 1, 7, " 次")

        self.overtime_button.setProperty("variant", "ghost")
        self.overtime_button.clicked.connect(self.overtime_requested.emit)
        self.save_button.clicked.connect(self._emit_save)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)

        eyebrow = QLabel("执行策略")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("提醒 / 惩罚 / 例外")
        title.setObjectName("cardTitleInline")
        copy = QLabel("临时加班会消耗本周名额，取消关机会进入惩罚等待。")
        copy.setObjectName("inlineHelperText")
        copy.setWordWrap(False)
        copy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(title)
        title_row.addWidget(copy, 1)
        title_row.setAlignment(copy, Qt.AlignmentFlag.AlignVCenter)

        metrics_box = QWidget()
        self._register_scaled_height(metrics_box, 114)
        metrics_grid = QGridLayout(metrics_box)
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        metrics_grid.setHorizontalSpacing(12)
        metrics_grid.setVerticalSpacing(8)
        metrics_grid.addWidget(self._metric_edit_tile("全屏警告", self.fullscreen_seconds), 0, 0)
        metrics_grid.addWidget(self._metric_edit_tile("取消惩罚", self.penalty_seconds), 0, 1)
        metrics_grid.addWidget(self._metric_edit_tile("单次加班", self.overtime_minutes), 1, 0)
        metrics_grid.addWidget(self._metric_edit_tile("每周上限", self.weekly_limit), 1, 1)
        metrics_grid.setColumnStretch(0, 1)
        metrics_grid.setColumnStretch(1, 1)

        self.unlock_strategy_button.setProperty("variant", "ghost")
        self.unlock_strategy_button.clicked.connect(self._request_strategy_unlock)

        toggle_box = subtle_panel()
        self._register_scaled_height(toggle_box, 52)
        toggle_layout = QHBoxLayout(toggle_box)
        toggle_layout.setContentsMargins(16, 5, 16, 5)
        toggle_layout.setSpacing(10)
        toggle_layout.addWidget(self.unlock_strategy_button)
        toggle_layout.addStretch(1)
        toggle_layout.addWidget(self.launch_on_startup)
        toggle_layout.addWidget(self.top_bar_on_top)

        self.control_note.setObjectName("helperTextStrong")
        self.control_note.setWordWrap(True)
        self.control_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        record_box = self._build_record_table()

        button_row = QHBoxLayout()
        button_row.setSpacing(14)
        button_row.addWidget(self.overtime_button)
        button_row.addWidget(self.control_note, 1)
        button_row.addWidget(self.save_button)

        layout.addWidget(eyebrow)
        layout.addLayout(title_row)
        layout.addWidget(metrics_box)
        layout.addWidget(toggle_box)
        layout.addWidget(record_box)
        layout.addLayout(button_row)

    def _set_schedule_editable(self, unlocked: bool) -> None:
        self._schedule_unlocked = unlocked
        for widget in (
            self.weekday_warning,
            self.weekday_shutdown,
            self.weekend_warning,
            self.weekend_shutdown,
        ):
            widget.setEnabled(unlocked)

        if unlocked:
            self.unlock_schedule_button.setText("时间已解锁")
            self.schedule_note.setText("本次已经允许修改时间，改完后记得点“保存设置”。")
        else:
            self.unlock_schedule_button.setText("修改时间")
            self.schedule_note.setText("默认锁定。先看 30 秒狠话，再决定要不要放宽规则。")

    def _set_strategy_editable(self, unlocked: bool) -> None:
        self._strategy_unlocked = unlocked
        for widget in (
            self.fullscreen_seconds,
            self.penalty_seconds,
            self.overtime_minutes,
            self.weekly_limit,
        ):
            widget.setEnabled(unlocked)

        if unlocked:
            self.unlock_strategy_button.setText("参数已解锁")
        else:
            self.unlock_strategy_button.setText("解锁参数")

    def _request_schedule_unlock(self) -> None:
        if self._schedule_unlocked:
            return
        dialog = TimeEditGateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._set_schedule_editable(True)
            self._schedule_dirty = False

    def _request_strategy_unlock(self) -> None:
        if self._strategy_unlocked:
            return
        dialog = TimeEditGateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._set_strategy_editable(True)
            self._settings_dirty = False

    def _time(self, value: str) -> QTime:
        return QTime.fromString(value, "HH:mm")

    def _settings_from_form(self) -> Settings:
        settings = self._latest_snapshot.settings
        settings.weekday.warning_time = self.weekday_warning.time().toString("HH:mm")
        settings.weekday.shutdown_time = self.weekday_shutdown.time().toString("HH:mm")
        settings.weekend.warning_time = self.weekend_warning.time().toString("HH:mm")
        settings.weekend.shutdown_time = self.weekend_shutdown.time().toString("HH:mm")
        settings.fullscreen_seconds = self.fullscreen_seconds.value()
        settings.penalty_seconds = self.penalty_seconds.value()
        settings.overtime_minutes = self.overtime_minutes.value()
        settings.weekly_overtime_limit = self.weekly_limit.value()
        settings.launch_on_startup = self.launch_on_startup.isChecked()
        settings.top_bar_always_on_top = self.top_bar_on_top.isChecked()
        return settings

    def _emit_save(self) -> None:
        self.settings_saved.emit(self._settings_from_form())

    def _toggle_favorite(self) -> None:
        if not self._latest_snapshot.quote_id:
            return
        self.favorite_toggled.emit(
            self._latest_snapshot.quote_id,
            not self._latest_snapshot.quote_is_favorite,
        )

    def _stage_text(self, stage: str) -> str:
        return {
            "idle": "准备收尾",
            "warning": "开始收尾",
            "fullscreen": "执行关机",
            "penalty": "惩罚等待",
            "overtime": "临时加班",
        }.get(stage, stage)

    def _set_record_cell(self, period_label: str, column: str, value: str) -> None:
        cell = self.record_cells.get(f"{period_label}:{column}")
        if cell is not None:
            cell.setText(value)

    def _apply_snapshot(self, snapshot: Snapshot) -> None:
        self._latest_snapshot = snapshot
        self.stage_value.setText(self._stage_text(snapshot.stage))
        self.remaining_value.setText(snapshot.remaining_label)
        self.now_value.setText(snapshot.now_label)

        self.quote_text.setText(snapshot.quote)
        self.favorite_button.setText("取消收藏" if snapshot.quote_is_favorite else "收藏这句")
        self.streak_value[1].setText(str(snapshot.streak))
        self.overtime_value[1].setText(f"{snapshot.weekly_overtime_used}/{snapshot.weekly_overtime_limit}")
        self.shutdown_value[1].setText(snapshot.planned_shutdown_time)
        self.control_note.setText(f"已申请 {snapshot.weekly_overtime_used}/{snapshot.weekly_overtime_limit} 次")
        for record in snapshot.record_stats:
            self._set_record_cell(record.period_label, "on_time", str(record.on_time_count))
            self._set_record_cell(record.period_label, "late", str(record.late_count))
            self._set_record_cell(record.period_label, "ratio", f"{record.late_ratio * 100:.0f}%")

        self._syncing_form = True
        try:
            if not self._schedule_dirty:
                self.weekday_warning.setTime(self._time(snapshot.today_weekday_warning_time))
                self.weekday_shutdown.setTime(self._time(snapshot.today_weekday_shutdown_time))
                self.weekend_warning.setTime(self._time(snapshot.today_weekend_warning_time))
                self.weekend_shutdown.setTime(self._time(snapshot.today_weekend_shutdown_time))

            if not self._settings_dirty:
                self.fullscreen_seconds.setValue(snapshot.settings.fullscreen_seconds)
                self.penalty_seconds.setValue(snapshot.settings.penalty_seconds)
                self.overtime_minutes.setValue(snapshot.settings.overtime_minutes)
                self.weekly_limit.setValue(snapshot.settings.weekly_overtime_limit)
                self.launch_on_startup.setChecked(snapshot.settings.launch_on_startup)
                self.top_bar_on_top.setChecked(snapshot.settings.top_bar_always_on_top)
        finally:
            self._syncing_form = False

        if self._schedule_matches_snapshot(snapshot):
            self._schedule_dirty = False

        if self._settings_match_snapshot(snapshot):
            self._settings_dirty = False

    def update_snapshot(self, snapshot: Snapshot) -> None:
        self._apply_snapshot(snapshot)

    def _schedule_matches_snapshot(self, snapshot: Snapshot) -> bool:
        return (
            self.weekday_warning.time().toString("HH:mm") == snapshot.today_weekday_warning_time
            and self.weekday_shutdown.time().toString("HH:mm") == snapshot.today_weekday_shutdown_time
            and self.weekend_warning.time().toString("HH:mm") == snapshot.today_weekend_warning_time
            and self.weekend_shutdown.time().toString("HH:mm") == snapshot.today_weekend_shutdown_time
        )

    def _settings_match_snapshot(self, snapshot: Snapshot) -> bool:
        return (
            self.fullscreen_seconds.value() == snapshot.settings.fullscreen_seconds
            and self.penalty_seconds.value() == snapshot.settings.penalty_seconds
            and self.overtime_minutes.value() == snapshot.settings.overtime_minutes
            and self.weekly_limit.value() == snapshot.settings.weekly_overtime_limit
            and self.launch_on_startup.isChecked() == snapshot.settings.launch_on_startup
            and self.top_bar_on_top.isChecked() == snapshot.settings.top_bar_always_on_top
        )

    def _apply_scale(self) -> None:
        width_scale = self.width() / DESIGN_WIDTH
        height_scale = self.height() / DESIGN_HEIGHT
        scale = max(0.74, min(1.0, min(width_scale, height_scale)))
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_app_style(scale))
        for widget, base_height in self._scaled_heights:
            widget.setFixedHeight(max(28, round(base_height * scale)))
        for widget, base_width in self._scaled_widths:
            widget.setFixedWidth(max(110, round(base_width * scale)))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_scale()

    def changeEvent(self, event) -> None:  # type: ignore[override]
        super().changeEvent(event)
        if (
            not self._allow_close
            and event.type() == QEvent.Type.WindowStateChange
            and self.isMinimized()
        ):
            QTimer.singleShot(0, self._hide_to_tray)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._allow_close:
            event.accept()
            return
        event.ignore()
        self._hide_to_tray()

    def _hide_to_tray(self) -> None:
        if self.isMinimized():
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.hide()

    def prepare_to_quit(self) -> None:
        self._allow_close = True

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Sleep Coach", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Sleep Coach", message)
