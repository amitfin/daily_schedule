"""Schedule and time range logic."""

from __future__ import annotations

import datetime
from typing import Any

from .const import CONF_DISABLED, CONF_FROM, CONF_TO

MIDNIGHT = datetime.time()


class TimeRange:
    """Time range."""

    def __init__(self, from_: datetime.time, to: datetime.time) -> None:
        """Initialize the object."""
        self.from_: datetime.time = from_
        self._from_offset = from_.hour * 3600 + from_.minute * 60 + from_.second
        self.to: datetime.time = to
        self._to_offset = to.hour * 3600 + to.minute * 60 + to.second
        self.wrap = self.to <= self.from_
        self.seconds = (
            self._to_offset - self._from_offset
            if not self.wrap
            else 86400 - self._from_offset + self._to_offset
        )

    def __eq__(self, other: TimeRange) -> bool:
        """Compare two TimeRanges."""
        return self.from_ == other.from_ and self.to == other.to

    def __gt__(self, other: TimeRange) -> bool:
        """Compare two TimeRanges."""
        if self.from_ != other.from_:
            return self.from_ > other.from_
        return self.seconds > other.seconds

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        if self.wrap:
            return self.from_ <= time or time < self.to

        return self.from_ <= time < self.to


class TimeRangeConfig(TimeRange):
    """Time range configuration."""

    def __init__(self, from_: str, to: str, disabled: bool) -> None:  # noqa: FBT001
        """Initialize the object."""
        super().__init__(
            datetime.time.fromisoformat(from_), datetime.time.fromisoformat(to)
        )
        self.disabled = disabled

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        return not self.disabled and super().containing(time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the object as a dict."""
        return {
            CONF_FROM: self.from_.isoformat(),
            CONF_TO: self.to.isoformat(),
            **({CONF_DISABLED: True} if self.disabled else {}),
        }


class Schedule:
    """List of TimeRange."""

    def __init__(self, schedule: list[dict[str, Any]]) -> None:
        """Create a list of TimeRanges representing the schedule."""
        self._config = sorted(
            [
                TimeRangeConfig(
                    time_range[CONF_FROM],
                    time_range[CONF_TO],
                    time_range.get(CONF_DISABLED, False),
                )
                for time_range in schedule
            ]
        )
        self._calculate_schedule()

    def _calculate_schedule(self) -> None:
        """Calculate the schedule."""
        schedule = []

        # Break wrap time ranges into two separate time ranges.
        for time_range in self._config:
            if time_range.disabled:
                continue
            if not time_range.wrap:
                schedule.append(TimeRange(time_range.from_, time_range.to))
            else:
                schedule.append(TimeRange(time_range.from_, MIDNIGHT))
                schedule.append(TimeRange(MIDNIGHT, time_range.to))
        schedule.sort()

        # Merge overlapping time ranges.
        self._schedule = []
        while len(schedule):
            from_range = schedule.pop(0)
            to_range = from_range
            while len(schedule) and (
                schedule[0].from_ <= to_range.to or to_range.to == MIDNIGHT
            ):
                if (
                    schedule[0].to > to_range.to or schedule[0].to == MIDNIGHT
                ) and to_range.to != MIDNIGHT:
                    to_range = schedule[0]
                schedule.pop(0)
            self._schedule.append(TimeRange(from_range.from_, to_range.to))

        if not self._schedule:
            return

        # Calculate on and off transitions.
        self._to_on = [time_range.from_ for time_range in self._schedule]
        self._to_off = [time_range.to for time_range in self._schedule]
        if self._to_on[0] == MIDNIGHT and self._to_off[-1] == MIDNIGHT:
            self._to_on.pop(0)
            self._to_off.pop(-1)

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        return any(time_range.containing(time) for time_range in self._schedule)

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize the object as a list."""
        return [time_range.to_dict() for time_range in self._config]

    def next_update(self, date: datetime.datetime) -> datetime.datetime | None:
        """Schedule a timer for the point when the state should be changed."""
        if not self._schedule:
            return None

        timestamps = self._to_off if self.containing(date.time()) else self._to_on
        if not timestamps:
            # If time ranges cover the entire day (the subtraction result is empty).
            return None

        time = date.time()
        prev = MIDNIGHT
        today = date.date()

        # Find the smallest timestamp which is bigger than time.
        for current in timestamps:
            if prev <= time < current:
                return datetime.datetime.combine(today, current, tzinfo=date.tzinfo)
            prev = current

        # Time is bigger than all timestamps. Use tomorrow's 1st timestamp.
        return datetime.datetime.combine(
            today + datetime.timedelta(days=1), timestamps[0], tzinfo=date.tzinfo
        )

    def next_updates(
        self, date: datetime.datetime, count: int
    ) -> list[datetime.datetime]:
        """Get list of future updates."""
        updates = []
        update = self.next_update(date)
        while len(updates) < count and update is not None:
            updates.append(update)
            update = self.next_update(update)
        return updates
