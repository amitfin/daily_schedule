"""Schedule and time range logic."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.const import (
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)
from homeassistant.exceptions import IntegrationError
from homeassistant.helpers import sun
from homeassistant.util.dt import as_local, now

from .const import CONF_DISABLED, CONF_FROM, CONF_TO, SUNRISE_SYMBOL, SUNSET_SYMBOL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

MIDNIGHT = datetime.time()


class TimeRange:
    """Time range."""

    def __init__(self, from_: datetime.time, to: datetime.time) -> None:
        """Initialize the object."""
        self.from_: datetime.time = from_
        self._from_offset = from_.hour * 3600 + from_.minute * 60 + from_.second
        self.to: datetime.time = to
        self._to_offset = to.hour * 3600 + to.minute * 60 + to.second
        self.reversed = self.to <= self.from_
        self.seconds = (
            self._to_offset - self._from_offset
            if not self.reversed
            else 86400 - self._from_offset + self._to_offset
        )

    def __eq__(self, other: object) -> bool:
        """Compare two TimeRanges."""
        if not isinstance(other, TimeRange):
            return NotImplemented
        return self.from_ == other.from_ and self.to == other.to

    def __gt__(self, other: object) -> bool:
        """Compare two TimeRanges."""
        if not isinstance(other, TimeRange):
            return NotImplemented
        if self.from_ != other.from_:
            return self.from_ > other.from_
        return self.seconds > other.seconds

    def __hash__(self) -> int:
        """Return a number unique to this range."""
        return hash((self._from_offset, self._to_offset))

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        if self.reversed:
            return self.from_ <= time or time < self.to

        return self.from_ <= time < self.to

    def to_dict(self) -> dict[str, Any]:
        """Serialize the object as a dict."""
        return {
            CONF_FROM: self.from_.isoformat(),
            CONF_TO: self.to.isoformat(),
        }


class TimeRangeConfig(TimeRange):
    """Time range configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        from_: str,
        to: str,
        disabled: bool,  # noqa: FBT001
    ) -> None:
        """Initialize the object."""
        self._dynamic_from, from_time = self.resolve_dynamic(hass, from_)
        self._dynamic_to, to_time = self.resolve_dynamic(hass, to)
        super().__init__(from_time, to_time)
        self.disabled = disabled

    def resolve_dynamic(
        self, hass: HomeAssistant, value: str
    ) -> tuple[str | None, datetime.time]:
        """Resolve dynamic time range."""
        if not value.startswith((SUNRISE_SYMBOL, SUNSET_SYMBOL)):
            return None, datetime.time.fromisoformat(value)

        if (
            event := sun.get_astral_event_date(
                hass,
                SUN_EVENT_SUNRISE if value[0] == SUNRISE_SYMBOL else SUN_EVENT_SUNSET,
            )
        ) is None:
            # Should never happen, but the above call can return None.
            error_message = "Unable to resolve sunrise/sunset time."
            raise IntegrationError(error_message)
        time = as_local(event).time().replace(microsecond=0, tzinfo=None)
        offset = int(value[1:]) if len(value) > 1 else 0

        if offset == 0:
            return value[:1], time

        time = (
            datetime.datetime.combine(now().date(), time)
            + datetime.timedelta(minutes=offset)
        ).time()
        return f"{value[0]}{offset:+}", time

    def is_dynamic(self) -> bool:
        """Check if the time range is dynamic."""
        return self._dynamic_from is not None or self._dynamic_to is not None

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        return not self.disabled and super().containing(time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the object as a dict."""
        return {
            CONF_FROM: self.from_.isoformat()
            if self._dynamic_from is None
            else self._dynamic_from,
            CONF_TO: self.to.isoformat()
            if self._dynamic_to is None
            else self._dynamic_to,
            **({CONF_DISABLED: True} if self.disabled else {}),
        }

    def to_dict_absolute(self) -> dict[str, Any]:
        """Serialize the object as a dict after sunrise/sunset resolution."""
        return super().to_dict()


class Schedule:
    """List of TimeRange."""

    def __init__(
        self,
        hass: HomeAssistant,
        schedule: list[dict[str, Any]],
        skip_reversed: bool,  # noqa: FBT001
    ) -> None:
        """Create a list of TimeRanges representing the schedule."""
        self._config = sorted(
            [
                TimeRangeConfig(
                    hass,
                    time_range[CONF_FROM],
                    time_range[CONF_TO],
                    time_range.get(CONF_DISABLED, False),
                )
                for time_range in schedule
            ]
        )
        self._skip_reversed = skip_reversed
        self._calculate_schedule()

    def _calculate_schedule(self) -> None:
        """Calculate the schedule."""
        self._schedule = []

        # There is nothing to do for a single time range.
        if len(self._config) == 1:
            if not self._config[0].disabled and (
                not self._config[0].reversed or not self._skip_reversed
            ):
                self._schedule.append(
                    TimeRange(self._config[0].from_, self._config[0].to)
                )
        else:
            # Break reversed time ranges into two separate time ranges.
            schedule = []
            for time_range in self._config:
                if time_range.disabled or (time_range.reversed and self._skip_reversed):
                    continue
                if not time_range.reversed or time_range.to == MIDNIGHT:
                    schedule.append(TimeRange(time_range.from_, time_range.to))
                else:
                    schedule.append(TimeRange(time_range.from_, MIDNIGHT))
                    schedule.append(TimeRange(MIDNIGHT, time_range.to))
            schedule.sort()

            # Merge overlapping time ranges.
            while schedule:
                from_range = schedule.pop(0)
                to_range = from_range
                while schedule and (
                    schedule[0].from_ <= to_range.to or to_range.to == MIDNIGHT
                ):
                    if (
                        schedule[0].to > to_range.to or schedule[0].to == MIDNIGHT
                    ) and to_range.to != MIDNIGHT:
                        to_range = schedule[0]
                    schedule.pop(0)
                self._schedule.append(TimeRange(from_range.from_, to_range.to))

            # Merge the first and last time ranges if they are adjusting.
            if (
                len(self._schedule) > 1
                and self._schedule[0].from_ == MIDNIGHT
                and self._schedule[-1].to == MIDNIGHT
            ):
                self._schedule[-1] = TimeRange(
                    self._schedule[-1].from_, self._schedule[0].to
                )
                self._schedule.pop(0)

        # Calculate on and off transitions.
        self._to_on = [time_range.from_ for time_range in self._schedule]
        self._to_off = [time_range.to for time_range in self._schedule]
        if self._schedule and self._to_on[0] == self._to_off[-1]:
            self._to_on.pop(0)
            self._to_off.pop(-1)
        self._to_on.sort()
        self._to_off.sort()

    def is_dynamic(self) -> bool:
        """Check if the schedule contains at least one dynamic time."""
        return any(time_range_config.is_dynamic() for time_range_config in self._config)

    def containing(self, time: datetime.time) -> bool:
        """Check if the time is inside the range."""
        return any(time_range.containing(time) for time_range in self._schedule)

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize the object as a list."""
        return [time_range.to_dict() for time_range in self._config]

    def to_list_absolute(self) -> list[dict[str, Any]]:
        """Serialize schedule as a list using absolute time (without sunrise/sunset)."""
        return [time_range.to_dict() for time_range in self._schedule]

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
        updates: list[datetime.datetime] = []
        update = self.next_update(date)
        while len(updates) < count and update is not None:
            updates.append(update)
            update = self.next_update(update)
        return updates
