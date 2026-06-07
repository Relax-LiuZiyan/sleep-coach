from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Stage = Literal["idle", "warning", "fullscreen", "penalty", "overtime"]
QuoteIntensity = Literal["light", "medium", "heavy"]


@dataclass(slots=True)
class DaySchedule:
    warning_time: str
    shutdown_time: str


@dataclass(slots=True)
class WeekendSchedule(DaySchedule):
    latest_shutdown_time: str


@dataclass(slots=True)
class Settings:
    weekday: DaySchedule
    weekend: WeekendSchedule
    fullscreen_seconds: int
    penalty_seconds: int
    overtime_minutes: int
    weekly_overtime_limit: int
    top_bar_x: int | None
    top_bar_y: int | None
    launch_on_startup: bool
    top_bar_always_on_top: bool


@dataclass(slots=True)
class Quote:
    quote_id: str
    text: str
    intensity: QuoteIntensity
    is_system: bool
    is_favorite: bool
    weight: int
    last_shown_on: str | None


@dataclass(slots=True)
class RecordStats:
    period_label: str
    on_time_count: int
    late_count: int
    total_count: int
    late_ratio: float


@dataclass(slots=True)
class Snapshot:
    stage: Stage
    remaining_label: str
    quote: str
    quote_id: str | None
    quote_is_favorite: bool
    now_label: str
    is_weekend: bool
    streak: int
    weekly_overtime_used: int
    weekly_overtime_limit: int
    fullscreen_countdown_label: str
    penalty_countdown_label: str
    planned_shutdown_time: str
    today_weekday_warning_time: str
    today_weekday_shutdown_time: str
    today_weekend_warning_time: str
    today_weekend_shutdown_time: str
    record_stats: list[RecordStats]
    settings: Settings


def default_settings() -> Settings:
    return Settings(
        weekday=DaySchedule(warning_time="23:10", shutdown_time="23:15"),
        weekend=WeekendSchedule(
            warning_time="23:30",
            shutdown_time="00:00",
            latest_shutdown_time="00:00",
        ),
        fullscreen_seconds=60,
        penalty_seconds=45,
        overtime_minutes=45,
        weekly_overtime_limit=2,
        top_bar_x=None,
        top_bar_y=12,
        launch_on_startup=True,
        top_bar_always_on_top=True,
    )
