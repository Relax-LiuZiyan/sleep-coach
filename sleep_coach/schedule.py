from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Settings, Stage

LATE_NIGHT_WRAP_HOUR = 5


def parse_clock(value: str) -> tuple[int, int]:
    hours_text, minutes_text = value.split(":")
    hours = int(hours_text)
    minutes = int(minutes_text)
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid clock time: {value}")
    return hours, minutes


def to_clock_minutes(value: str) -> int:
    hours, minutes = parse_clock(value)
    total = hours * 60 + minutes
    return total + 1440 if hours < LATE_NIGHT_WRAP_HOUR else total


def schedule_date(now: datetime) -> datetime:
    target = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now.hour < LATE_NIGHT_WRAP_HOUR:
        target -= timedelta(days=1)
    return target


def date_key(now: datetime) -> str:
    return schedule_date(now).date().isoformat()


def week_key(now: datetime) -> str:
    current = schedule_date(now)
    weekday = current.weekday()
    monday = current - timedelta(days=weekday)
    return monday.date().isoformat()


def now_minutes(now: datetime) -> int:
    total = now.hour * 60 + now.minute
    return total + 1440 if now.hour < LATE_NIGHT_WRAP_HOUR else total


def is_weekend_schedule(now: datetime) -> bool:
    return schedule_date(now).weekday() in {4, 5}


def format_duration_minutes(value: int) -> str:
    safe = max(0, value)
    hours = safe // 60
    minutes = safe % 60
    if hours <= 0:
        return f"还有 {minutes} 分钟"
    return f"还有 {hours} 小时 {minutes} 分钟"


def format_hms_from_seconds(total_seconds: int) -> str:
    safe = max(0, total_seconds)
    hours = safe // 3600
    minutes = (safe % 3600) // 60
    seconds = safe % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_countdown(seconds: int) -> str:
    safe = max(0, seconds)
    minutes = safe // 60
    remainder = safe % 60
    return f"{minutes}:{remainder:02d}"


def time_label(now: datetime) -> str:
    return now.strftime("%H:%M")


def time_label_with_seconds(now: datetime) -> str:
    return now.strftime("%H:%M:%S")


@dataclass(slots=True)
class ScheduleState:
    stage: Stage
    is_weekend: bool
    warning_time: str
    shutdown_time: str
    remaining_label: str
    remaining_seconds_label: str


def build_schedule_state(
    *,
    now: datetime,
    settings: Settings,
    overtime_active_until: datetime | None,
    dismissed_for_tonight: bool,
) -> ScheduleState:
    weekend = is_weekend_schedule(now)
    warning_time = settings.weekend.warning_time if weekend else settings.weekday.warning_time
    shutdown_time = settings.weekend.shutdown_time if weekend else settings.weekday.shutdown_time

    if dismissed_for_tonight:
        return ScheduleState(
            stage="idle",
            is_weekend=weekend,
            warning_time=warning_time,
            shutdown_time=shutdown_time,
            remaining_label="今晚流程已结束",
            remaining_seconds_label="00:00:00",
        )

    if overtime_active_until and overtime_active_until > now:
        seconds_left = int((overtime_active_until - now).total_seconds())
        return ScheduleState(
            stage="overtime",
            is_weekend=weekend,
            warning_time=warning_time,
            shutdown_time=shutdown_time,
            remaining_label=format_duration_minutes(seconds_left // 60),
            remaining_seconds_label=format_hms_from_seconds(seconds_left),
        )

    current_minutes = now_minutes(now)
    warning_minutes = to_clock_minutes(warning_time)
    shutdown_minutes = to_clock_minutes(shutdown_time)

    if current_minutes >= shutdown_minutes:
        return ScheduleState(
            stage="fullscreen",
            is_weekend=weekend,
            warning_time=warning_time,
            shutdown_time=shutdown_time,
            remaining_label="现在就该下线了",
            remaining_seconds_label="00:00:00",
        )

    if current_minutes >= warning_minutes:
        shutdown_point = schedule_date(now).replace(
            hour=parse_clock(shutdown_time)[0],
            minute=parse_clock(shutdown_time)[1],
            second=0,
            microsecond=0,
        )
        if parse_clock(shutdown_time)[0] < LATE_NIGHT_WRAP_HOUR:
            shutdown_point += timedelta(days=1)
        seconds_left = int((shutdown_point - now).total_seconds())
        return ScheduleState(
            stage="warning",
            is_weekend=weekend,
            warning_time=warning_time,
            shutdown_time=shutdown_time,
            remaining_label=format_duration_minutes(shutdown_minutes - current_minutes),
            remaining_seconds_label=format_hms_from_seconds(seconds_left),
        )

    warning_point = schedule_date(now).replace(
        hour=parse_clock(warning_time)[0],
        minute=parse_clock(warning_time)[1],
        second=0,
        microsecond=0,
    )
    if parse_clock(warning_time)[0] < LATE_NIGHT_WRAP_HOUR:
        warning_point += timedelta(days=1)
    seconds_left = int((warning_point - now).total_seconds())
    return ScheduleState(
        stage="idle",
        is_weekend=weekend,
        warning_time=warning_time,
        shutdown_time=shutdown_time,
        remaining_label=format_duration_minutes(warning_minutes - current_minutes),
        remaining_seconds_label=format_hms_from_seconds(seconds_left),
    )
