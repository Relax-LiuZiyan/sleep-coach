from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from .models import Quote, RecordStats, Settings, default_settings
from .quotes import DEFAULT_QUOTES
from .schedule import to_clock_minutes


class Storage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "sleep_coach.db"
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._bootstrap()

    def _bootstrap(self) -> None:
        cursor = self.connection.cursor()
        cursor.executescript(
            """
            create table if not exists settings (
                id integer primary key check (id = 1),
                value text not null
            );

            create table if not exists sleep_records (
                date text primary key,
                is_weekend integer not null,
                planned_shutdown_time text not null,
                actual_sleep_time text,
                status text not null,
                cancel_count integer not null default 0,
                overtime_count integer not null default 0
            );

            create table if not exists quotes (
                quote_id text primary key,
                text_value text not null,
                intensity text not null,
                is_system integer not null,
                is_favorite integer not null default 0,
                weight integer not null default 1,
                last_shown_on text
            );

            create table if not exists schedule_overrides (
                date text primary key,
                weekday_warning_time text not null,
                weekday_shutdown_time text not null,
                weekend_warning_time text not null,
                weekend_shutdown_time text not null
            );
            """
        )
        self.connection.commit()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        if self.connection.execute("select 1 from settings where id = 1").fetchone() is None:
            self.connection.execute(
                "insert into settings (id, value) values (1, ?)",
                (json.dumps(self._settings_to_dict(default_settings())),),
            )

        for quote_id, text, intensity, weight in DEFAULT_QUOTES:
            self.connection.execute(
                """
                insert into quotes (quote_id, text_value, intensity, is_system, is_favorite, weight, last_shown_on)
                values (?, ?, ?, 1, 0, ?, null)
                on conflict(quote_id) do update set
                    text_value = excluded.text_value,
                    intensity = excluded.intensity,
                    is_system = excluded.is_system,
                    weight = excluded.weight
                """,
                (quote_id, text, intensity, weight),
            )

        self.connection.commit()

    def _settings_to_dict(self, settings: Settings) -> dict[str, object]:
        return {
            "weekday": {
                "warning_time": settings.weekday.warning_time,
                "shutdown_time": settings.weekday.shutdown_time,
            },
            "weekend": {
                "warning_time": settings.weekend.warning_time,
                "shutdown_time": settings.weekend.shutdown_time,
                "latest_shutdown_time": settings.weekend.latest_shutdown_time,
            },
            "fullscreen_seconds": settings.fullscreen_seconds,
            "penalty_seconds": settings.penalty_seconds,
            "overtime_minutes": settings.overtime_minutes,
            "weekly_overtime_limit": settings.weekly_overtime_limit,
            "top_bar_x": settings.top_bar_x,
            "top_bar_y": settings.top_bar_y,
            "launch_on_startup": settings.launch_on_startup,
            "top_bar_always_on_top": settings.top_bar_always_on_top,
        }

    def _settings_from_row(self, row: sqlite3.Row) -> Settings:
        raw = json.loads(row["value"])
        defaults = default_settings()
        return Settings(
            weekday=defaults.weekday.__class__(
                warning_time=raw["weekday"]["warning_time"],
                shutdown_time=raw["weekday"]["shutdown_time"],
            ),
            weekend=defaults.weekend.__class__(
                warning_time=raw["weekend"]["warning_time"],
                shutdown_time=raw["weekend"]["shutdown_time"],
                latest_shutdown_time=raw["weekend"]["latest_shutdown_time"],
            ),
            fullscreen_seconds=int(raw["fullscreen_seconds"]),
            penalty_seconds=int(raw["penalty_seconds"]),
            overtime_minutes=int(raw["overtime_minutes"]),
            weekly_overtime_limit=int(raw["weekly_overtime_limit"]),
            top_bar_x=raw.get("top_bar_x"),
            top_bar_y=raw.get("top_bar_y"),
            launch_on_startup=bool(raw["launch_on_startup"]),
            top_bar_always_on_top=bool(raw["top_bar_always_on_top"]),
        )

    def load_settings(self) -> Settings:
        row = self.connection.execute("select value from settings where id = 1").fetchone()
        if row is None:
            defaults = default_settings()
            self.save_settings(defaults)
            return defaults
        return self._settings_from_row(row)

    def save_settings(self, settings: Settings) -> Settings:
        if to_clock_minutes(settings.weekday.warning_time) >= to_clock_minutes(settings.weekday.shutdown_time):
            raise ValueError("工作日提醒时间必须早于关机时间。")
        if to_clock_minutes(settings.weekend.warning_time) > to_clock_minutes(settings.weekend.shutdown_time):
            raise ValueError("周末提醒时间必须早于或等于关机时间。")
        if to_clock_minutes(settings.weekend.shutdown_time) > to_clock_minutes(settings.weekend.latest_shutdown_time):
            raise ValueError("周末最晚不能超过 00:00。")

        self.connection.execute(
            """
            insert into settings (id, value) values (1, ?)
            on conflict(id) do update set value = excluded.value
            """,
            (json.dumps(self._settings_to_dict(settings)),),
        )
        self.connection.commit()
        return settings

    def load_schedule_override(self, day_key: str) -> dict[str, str] | None:
        row = self.connection.execute(
            """
            select weekday_warning_time, weekday_shutdown_time, weekend_warning_time, weekend_shutdown_time
            from schedule_overrides
            where date = ?
            """,
            (day_key,),
        ).fetchone()
        if row is None:
            return None
        return {
            "weekday_warning_time": row["weekday_warning_time"],
            "weekday_shutdown_time": row["weekday_shutdown_time"],
            "weekend_warning_time": row["weekend_warning_time"],
            "weekend_shutdown_time": row["weekend_shutdown_time"],
        }

    def save_schedule_override(self, day_key: str, override: dict[str, str]) -> None:
        self.connection.execute(
            """
            insert into schedule_overrides (
                date, weekday_warning_time, weekday_shutdown_time, weekend_warning_time, weekend_shutdown_time
            )
            values (?, ?, ?, ?, ?)
            on conflict(date) do update set
                weekday_warning_time = excluded.weekday_warning_time,
                weekday_shutdown_time = excluded.weekday_shutdown_time,
                weekend_warning_time = excluded.weekend_warning_time,
                weekend_shutdown_time = excluded.weekend_shutdown_time
            """,
            (
                day_key,
                override["weekday_warning_time"],
                override["weekday_shutdown_time"],
                override["weekend_warning_time"],
                override["weekend_shutdown_time"],
            ),
        )
        self.connection.commit()

    def list_quotes(self, intensity: str | None = None) -> list[Quote]:
        if intensity:
            rows = self.connection.execute(
                "select * from quotes where intensity = ? order by quote_id asc",
                (intensity,),
            ).fetchall()
        else:
            rows = self.connection.execute("select * from quotes order by quote_id asc").fetchall()
        return [
            Quote(
                quote_id=row["quote_id"],
                text=row["text_value"],
                intensity=row["intensity"],
                is_system=bool(row["is_system"]),
                is_favorite=bool(row["is_favorite"]),
                weight=int(row["weight"]),
                last_shown_on=row["last_shown_on"],
            )
            for row in rows
        ]

    def mark_quote_shown(self, quote_id: str, day_key: str) -> None:
        self.connection.execute(
            "update quotes set last_shown_on = ? where quote_id = ?",
            (day_key, quote_id),
        )
        self.connection.commit()

    def set_quote_favorite(self, quote_id: str, is_favorite: bool) -> None:
        self.connection.execute(
            "update quotes set is_favorite = ? where quote_id = ?",
            (1 if is_favorite else 0, quote_id),
        )
        self.connection.commit()

    def ensure_day(self, day_key: str, is_weekend: bool, planned_shutdown_time: str) -> None:
        self.connection.execute(
            """
            insert into sleep_records (date, is_weekend, planned_shutdown_time, status)
            values (?, ?, ?, 'pending')
            on conflict(date) do nothing
            """,
            (day_key, 1 if is_weekend else 0, planned_shutdown_time),
        )
        self.connection.commit()

    def mark_stale_pending_records(self, current_day_key: str) -> None:
        self.connection.execute(
            """
            update sleep_records
            set status = 'missed'
            where date < ?
              and status = 'pending'
              and actual_sleep_time is null
              and cancel_count = 0
              and overtime_count = 0
            """,
            (current_day_key,),
        )
        self.connection.commit()

    def mark_cancel(self, day_key: str, is_weekend: bool, planned_shutdown_time: str) -> None:
        self.ensure_day(day_key, is_weekend, planned_shutdown_time)
        self.connection.execute(
            """
            update sleep_records
            set cancel_count = cancel_count + 1, status = 'cancelled'
            where date = ?
            """,
            (day_key,),
        )
        self.connection.commit()

    def mark_overtime(self, day_key: str, is_weekend: bool, planned_shutdown_time: str) -> None:
        self.ensure_day(day_key, is_weekend, planned_shutdown_time)
        self.connection.execute(
            """
            update sleep_records
            set overtime_count = overtime_count + 1
            where date = ?
            """,
            (day_key,),
        )
        self.connection.commit()

    def mark_completed(self, day_key: str, is_weekend: bool, planned_shutdown_time: str, actual_sleep_time: str) -> None:
        self.ensure_day(day_key, is_weekend, planned_shutdown_time)
        self.connection.execute(
            """
            update sleep_records
            set actual_sleep_time = ?, status = 'completed'
            where date = ?
            """,
            (actual_sleep_time, day_key),
        )
        self.connection.commit()

    def weekly_overtime_usage(self, monday_key: str) -> int:
        monday = date.fromisoformat(monday_key)
        next_monday = monday + timedelta(days=7)
        row = self.connection.execute(
            """
            select coalesce(sum(overtime_count), 0) as total
            from sleep_records
            where date >= ? and date < ?
            """,
            (monday.isoformat(), next_monday.isoformat()),
        ).fetchone()
        return int(row["total"]) if row else 0

    def reset_weekly_overtime_usage(self, monday_key: str) -> None:
        monday = date.fromisoformat(monday_key)
        next_monday = monday + timedelta(days=7)
        self.connection.execute(
            """
            update sleep_records
            set overtime_count = 0
            where date >= ? and date < ?
            """,
            (monday.isoformat(), next_monday.isoformat()),
        )
        self.connection.commit()

    def _is_trackable_record(self, row: sqlite3.Row) -> bool:
        return (
            row["status"] != "pending"
            or row["actual_sleep_time"] is not None
            or int(row["cancel_count"]) > 0
            or int(row["overtime_count"]) > 0
        )

    def _is_late_record(self, row: sqlite3.Row) -> bool:
        if int(row["cancel_count"]) > 0 or int(row["overtime_count"]) > 0:
            return True

        actual_sleep_time = row["actual_sleep_time"]
        if actual_sleep_time:
            return to_clock_minutes(actual_sleep_time) > to_clock_minutes(row["planned_shutdown_time"])

        return row["status"] != "completed"

    def list_record_stats(self, today_key: str) -> list[RecordStats]:
        today = date.fromisoformat(today_key)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        rows = self.connection.execute(
            """
            select date, planned_shutdown_time, actual_sleep_time, status, cancel_count, overtime_count
            from sleep_records
            where date >= ?
            order by date desc
            """,
            (year_start.isoformat(),),
        ).fetchall()

        buckets = [
            ("本周", week_start),
            ("本月", month_start),
            ("本年", year_start),
        ]
        stats: list[RecordStats] = []

        for label, start_day in buckets:
            relevant = [
                row
                for row in rows
                if start_day <= date.fromisoformat(row["date"]) <= today and self._is_trackable_record(row)
            ]
            late_count = sum(1 for row in relevant if self._is_late_record(row))
            total_count = len(relevant)
            on_time_count = max(0, total_count - late_count)
            late_ratio = (late_count / total_count) if total_count else 0.0
            stats.append(
                RecordStats(
                    period_label=label,
                    on_time_count=on_time_count,
                    late_count=late_count,
                    total_count=total_count,
                    late_ratio=late_ratio,
                )
            )

        return stats

    def current_streak(self) -> int:
        rows = self.connection.execute(
            """
            select date
            from sleep_records
            where status = 'completed'
            order by date desc
            """
        ).fetchall()
        streak = 0
        previous: date | None = None
        for row in rows:
            current = date.fromisoformat(row["date"])
            if previous is None:
                streak += 1
                previous = current
                continue
            if current == previous - timedelta(days=1):
                streak += 1
                previous = current
            else:
                break
        return streak
