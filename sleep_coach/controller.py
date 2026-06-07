from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from .models import Quote, RecordStats, Settings, Snapshot
from .quotes import pick_quote_for_day
from .schedule import (
    build_schedule_state,
    date_key,
    format_countdown,
    time_label,
    time_label_with_seconds,
    to_clock_minutes,
    week_key,
)
from .storage import Storage
from .system import configure_launch_on_startup, perform_shutdown


class SleepCoachController(QObject):
    snapshot_changed = Signal(object)
    error_raised = Signal(str)

    def __init__(self, root: Path, project_root: Path) -> None:
        super().__init__()
        self.storage = Storage(root)
        self.project_root = project_root
        self.settings = self.storage.load_settings()
        self._recent_quote_ids: deque[str] = deque(maxlen=10)
        self._active_quote: Quote | None = None
        self._active_stage: str | None = None
        self._dismissed_day: str | None = None
        self._overtime_until: datetime | None = None
        self._fullscreen_until: datetime | None = None
        self._penalty_until: datetime | None = None
        self._snapshot = Snapshot(
            stage="idle",
            remaining_label="00:00:00",
            quote="正在启动你的夜间教练...",
            quote_id=None,
            quote_is_favorite=False,
            now_label="00:00:00",
            is_weekend=False,
            streak=0,
            weekly_overtime_used=0,
            weekly_overtime_limit=self.settings.weekly_overtime_limit,
            fullscreen_countdown_label=format_countdown(self.settings.fullscreen_seconds),
            penalty_countdown_label=format_countdown(self.settings.penalty_seconds),
            planned_shutdown_time=self.settings.weekday.shutdown_time,
            today_weekday_warning_time=self.settings.weekday.warning_time,
            today_weekday_shutdown_time=self.settings.weekday.shutdown_time,
            today_weekend_warning_time=self.settings.weekend.warning_time,
            today_weekend_shutdown_time=self.settings.weekend.shutdown_time,
            record_stats=[
                RecordStats(period_label="本周", on_time_count=0, late_count=0, total_count=0, late_ratio=0.0),
                RecordStats(period_label="本月", on_time_count=0, late_count=0, total_count=0, late_ratio=0.0),
                RecordStats(period_label="本年", on_time_count=0, late_count=0, total_count=0, late_ratio=0.0),
            ],
            settings=self.settings,
        )
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

    @property
    def snapshot(self) -> Snapshot:
        return self._snapshot

    def start(self) -> None:
        configure_launch_on_startup(self.settings.launch_on_startup, self.project_root)
        self.tick()
        self.timer.start()

    def _pick_quote(self, stage: str, day_key_value: str) -> Quote:
        if self._active_quote and self._active_stage == stage:
            return self._active_quote

        intensity = "light"
        if stage in {"warning", "overtime"}:
            intensity = "medium"
        elif stage in {"fullscreen", "penalty"}:
            intensity = "heavy"

        quotes = self.storage.list_quotes(intensity)
        quote = pick_quote_for_day(quotes, day_key_value, list(self._recent_quote_ids))
        self.storage.mark_quote_shown(quote.quote_id, day_key_value)
        self._recent_quote_ids.appendleft(quote.quote_id)
        quote.last_shown_on = day_key_value
        self._active_quote = quote
        self._active_stage = stage
        return quote

    def _reset_daily_if_needed(self, current_day: str) -> None:
        if self._dismissed_day and self._dismissed_day != current_day:
            self._dismissed_day = None
            self._active_quote = None
            self._active_stage = None

    def _effective_settings_for_day(self, current_day: str) -> tuple[Settings, dict[str, str]]:
        override = self.storage.load_schedule_override(current_day)
        values = {
            "weekday_warning_time": self.settings.weekday.warning_time,
            "weekday_shutdown_time": self.settings.weekday.shutdown_time,
            "weekend_warning_time": self.settings.weekend.warning_time,
            "weekend_shutdown_time": self.settings.weekend.shutdown_time,
        }
        if override:
            values.update(override)

        effective = Settings(
            weekday=self.settings.weekday.__class__(
                warning_time=values["weekday_warning_time"],
                shutdown_time=values["weekday_shutdown_time"],
            ),
            weekend=self.settings.weekend.__class__(
                warning_time=values["weekend_warning_time"],
                shutdown_time=values["weekend_shutdown_time"],
                latest_shutdown_time=self.settings.weekend.latest_shutdown_time,
            ),
            fullscreen_seconds=self.settings.fullscreen_seconds,
            penalty_seconds=self.settings.penalty_seconds,
            overtime_minutes=self.settings.overtime_minutes,
            weekly_overtime_limit=self.settings.weekly_overtime_limit,
            top_bar_x=self.settings.top_bar_x,
            top_bar_y=self.settings.top_bar_y,
            launch_on_startup=self.settings.launch_on_startup,
            top_bar_always_on_top=self.settings.top_bar_always_on_top,
        )
        return effective, values

    def tick(self) -> None:
        now = datetime.now()
        current_day = date_key(now)
        self.storage.mark_stale_pending_records(current_day)
        self._reset_daily_if_needed(current_day)
        effective_settings, today_values = self._effective_settings_for_day(current_day)
        state = build_schedule_state(
            now=now,
            settings=effective_settings,
            overtime_active_until=self._overtime_until,
            dismissed_for_tonight=self._dismissed_day == current_day,
        )

        self.storage.ensure_day(current_day, state.is_weekend, state.shutdown_time)

        stage = state.stage
        fullscreen_label = format_countdown(self.settings.fullscreen_seconds)
        penalty_label = format_countdown(self.settings.penalty_seconds)

        if self._penalty_until:
            remaining_penalty = int((self._penalty_until - now).total_seconds())
            if remaining_penalty > 0:
                stage = "penalty"
                penalty_label = format_countdown(remaining_penalty)
            else:
                self._penalty_until = None
                self._dismissed_day = current_day
                stage = "idle"

        if stage == "fullscreen":
            if self._fullscreen_until is None:
                self._fullscreen_until = now + timedelta(seconds=self.settings.fullscreen_seconds)
            remaining_fullscreen = int((self._fullscreen_until - now).total_seconds())
            if remaining_fullscreen > 0:
                fullscreen_label = format_countdown(remaining_fullscreen)
            else:
                self.sleep_now(trigger_shutdown=True)
                return
        else:
            self._fullscreen_until = None

        if self._overtime_until and self._overtime_until <= now:
            self._overtime_until = None

        quote = self._pick_quote(stage, current_day)
        self._snapshot = Snapshot(
            stage=stage,
            remaining_label=state.remaining_seconds_label,
            quote=quote.text,
            quote_id=quote.quote_id,
            quote_is_favorite=quote.is_favorite,
            now_label=time_label_with_seconds(now),
            is_weekend=state.is_weekend,
            streak=self.storage.current_streak(),
            weekly_overtime_used=self.storage.weekly_overtime_usage(week_key(now)),
            weekly_overtime_limit=self.settings.weekly_overtime_limit,
            fullscreen_countdown_label=fullscreen_label,
            penalty_countdown_label=penalty_label,
            planned_shutdown_time=state.shutdown_time,
            today_weekday_warning_time=today_values["weekday_warning_time"],
            today_weekday_shutdown_time=today_values["weekday_shutdown_time"],
            today_weekend_warning_time=today_values["weekend_warning_time"],
            today_weekend_shutdown_time=today_values["weekend_shutdown_time"],
            record_stats=self.storage.list_record_stats(current_day),
            settings=self.settings,
        )
        self.snapshot_changed.emit(self._snapshot)

    def save_settings(self, settings: Settings) -> None:
        try:
            current_day = date_key(datetime.now())
            if to_clock_minutes(settings.weekday.warning_time) >= to_clock_minutes(settings.weekday.shutdown_time):
                raise ValueError("今天的工作日提醒时间必须早于关机时间。")
            if to_clock_minutes(settings.weekend.warning_time) > to_clock_minutes(settings.weekend.shutdown_time):
                raise ValueError("今天的周末提醒时间必须早于或等于关机时间。")
            if to_clock_minutes(settings.weekend.shutdown_time) > to_clock_minutes(self.settings.weekend.latest_shutdown_time):
                raise ValueError("今天的周末最晚也不能超过 00:00。")

            self.storage.save_schedule_override(
                current_day,
                {
                    "weekday_warning_time": settings.weekday.warning_time,
                    "weekday_shutdown_time": settings.weekday.shutdown_time,
                    "weekend_warning_time": settings.weekend.warning_time,
                    "weekend_shutdown_time": settings.weekend.shutdown_time,
                },
            )

            global_settings = Settings(
                weekday=self.settings.weekday.__class__(
                    warning_time=self.settings.weekday.warning_time,
                    shutdown_time=self.settings.weekday.shutdown_time,
                ),
                weekend=self.settings.weekend.__class__(
                    warning_time=self.settings.weekend.warning_time,
                    shutdown_time=self.settings.weekend.shutdown_time,
                    latest_shutdown_time=self.settings.weekend.latest_shutdown_time,
                ),
                fullscreen_seconds=settings.fullscreen_seconds,
                penalty_seconds=settings.penalty_seconds,
                overtime_minutes=settings.overtime_minutes,
                weekly_overtime_limit=settings.weekly_overtime_limit,
                top_bar_x=self.settings.top_bar_x,
                top_bar_y=self.settings.top_bar_y,
                launch_on_startup=settings.launch_on_startup,
                top_bar_always_on_top=settings.top_bar_always_on_top,
            )
            self.settings = self.storage.save_settings(global_settings)
            configure_launch_on_startup(self.settings.launch_on_startup, self.project_root)
            self.tick()
        except ValueError as error:
            self.error_raised.emit(str(error))

    def request_overtime(self) -> tuple[bool, str]:
        now = datetime.now()
        used = self.storage.weekly_overtime_usage(week_key(now))
        if used >= self.settings.weekly_overtime_limit:
            return False, "本周临时加班次数已经用完了。"

        self._overtime_until = now + timedelta(minutes=self.settings.overtime_minutes)
        self._fullscreen_until = None
        self._penalty_until = None
        self._dismissed_day = None
        self.storage.mark_overtime(
            date_key(now),
            self.snapshot.is_weekend,
            self.snapshot.planned_shutdown_time,
        )
        self.tick()
        return True, "今晚已获得一次临时加班。"

    def cancel_shutdown(self) -> None:
        now = datetime.now()
        self._penalty_until = now + timedelta(seconds=self.settings.penalty_seconds)
        self._fullscreen_until = None
        self.storage.mark_cancel(
            date_key(now),
            self.snapshot.is_weekend,
            self.snapshot.planned_shutdown_time,
        )
        self.tick()

    def sleep_now(self, *, trigger_shutdown: bool = False) -> None:
        now = datetime.now()
        self.storage.mark_completed(
            date_key(now),
            self.snapshot.is_weekend,
            self.snapshot.planned_shutdown_time,
            time_label(now),
        )
        self._dismissed_day = date_key(now)
        self._fullscreen_until = None
        self._penalty_until = None
        self.tick()
        if trigger_shutdown:
            perform_shutdown()

    def set_favorite(self, quote_id: str, favorite: bool) -> None:
        self.storage.set_quote_favorite(quote_id, favorite)
        if self._active_quote and self._active_quote.quote_id == quote_id:
            self._active_quote.is_favorite = favorite
        self.tick()

    def update_top_bar_position(self, x: int, y: int) -> None:
        self.settings.top_bar_x = x
        self.settings.top_bar_y = y
        self.storage.save_settings(self.settings)
