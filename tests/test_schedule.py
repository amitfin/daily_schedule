"""The tests for the schedule class."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from homeassistant.exceptions import IntegrationError

from custom_components.daily_schedule.const import (
    CONF_DISABLED,
    CONF_FROM,
    CONF_TO,
    SUNRISE_SYMBOL,
    SUNSET_SYMBOL,
)
from custom_components.daily_schedule.schedule import (
    Schedule,
    TimeRange,
    TimeRangeConfig,
)

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    ("from1", "to1", "from2", "to2", "result"),
    [
        ("01:00", "02:00", "01:00", "02:00", False),
        ("01:01", "02:00", "01:00", "02:00", True),
        ("01:00", "02:01", "01:00", "02:00", True),
        ("01:00", "02:00", "01:01", "02:00", False),
    ],
    ids=["equal", "start", "length", "smaller"],
)
def test_greater_operator(
    from1: str,
    to1: str,
    from2: str,
    to2: str,
    result: bool,  # noqa: FBT001
) -> None:
    """Test comparison of TimeRange."""
    assert (
        TimeRange(datetime.time.fromisoformat(from1), datetime.time.fromisoformat(to1))
        > TimeRange(
            datetime.time.fromisoformat(from2), datetime.time.fromisoformat(to2)
        )
    ) is result


def test_different_object() -> None:
    """Test comparison of TimeRange with different object."""
    midnight = datetime.time.fromisoformat("00:00")
    assert TimeRange(midnight, midnight) != 1
    with pytest.raises(TypeError):
        assert TimeRange(midnight, midnight) > 1


def test_sort() -> None:
    """Test sorting of TimeRange."""
    time_ranges = [
        TimeRange(
            datetime.time.fromisoformat("02:00"), datetime.time.fromisoformat("03:00")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("01:30")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
        ),
    ]
    time_ranges.sort()
    assert time_ranges == [
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("01:30")
        ),
        TimeRange(
            datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
        ),
        TimeRange(
            datetime.time.fromisoformat("02:00"), datetime.time.fromisoformat("03:00")
        ),
    ]


def test_time_range_hash() -> None:
    """Test hashing function of time_range."""
    time_range1 = TimeRange(
        datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
    )
    time_range2 = TimeRange(
        datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:01")
    )
    time_range3 = TimeRange(
        datetime.time.fromisoformat("01:00"), datetime.time.fromisoformat("02:00")
    )
    assert hash(time_range1) == hash(time_range3)
    assert hash(time_range1) != hash(time_range2)


@pytest.mark.parametrize(
    ("start", "end", "time", "disabled", "result"),
    [
        ("05:00", "10:00", "05:00", False, True),
        ("05:00", "10:00", "10:00", False, False),
        ("22:00", "05:00", "23:00", False, True),
        ("22:00", "05:00", "04:00", False, True),
        ("22:00", "05:00", "12:00", False, False),
        ("00:00", "00:00", "00:00", False, True),
        ("00:00", "00:00", "00:00", True, False),
    ],
    ids=[
        "contained",
        "not contained",
        "cross day night",
        "cross day morning",
        "cross day not contained",
        "entire day",
        "entire day disabled",
    ],
)
def test_time_range(  # noqa: PLR0913
    hass: HomeAssistant,
    start: str,
    end: str,
    time: str,
    disabled: bool,  # noqa: FBT001
    result: bool,  # noqa: FBT001
) -> None:
    """Test for TimeRange class."""
    assert (
        TimeRangeConfig(hass, start, end, disabled).containing(
            datetime.time.fromisoformat(time)
        )
        is result
    )


@pytest.mark.parametrize(
    ("from_", "to", "from_absolute", "to_absolute", "from_string", "to_string"),
    [
        (
            SUNRISE_SYMBOL,
            SUNSET_SYMBOL,
            "05:54:37",
            "17:46:10",
            SUNRISE_SYMBOL,
            SUNSET_SYMBOL,
        ),
        ("↑+10", "↓-10", "06:04:37", "17:36:10", "↑+10", "↓-10"),
        ("↑+0", "↓-0", "05:54:37", "17:46:10", SUNRISE_SYMBOL, SUNSET_SYMBOL),
    ],
    ids=[
        "sunrise to sunset",
        "offsets",
        "zero offset",
    ],
)
async def test_dynamic_range(  # noqa: PLR0913
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    from_: str,
    to: str,
    from_absolute: str,
    to_absolute: str,
    from_string: str,
    to_string: str,
) -> None:
    """Test dynamic from and to."""
    freezer.move_to("2025-03-12T00:00:00")
    test = TimeRangeConfig(hass, from_, to, False)  # noqa: FBT003
    assert test.to_dict() == {CONF_FROM: from_string, CONF_TO: to_string}
    assert test.to_dict_absolute() == {CONF_FROM: from_absolute, CONF_TO: to_absolute}


@patch("homeassistant.helpers.sun.get_astral_event_date", return_value=None)
def test_sun_not_resolvable(_: Mock, hass: HomeAssistant) -> None:  # noqa: PT019
    """Test error when sun is not resolvable."""
    with pytest.raises(IntegrationError):
        TimeRangeConfig(hass, SUNRISE_SYMBOL, SUNSET_SYMBOL, False)  # noqa: FBT003


@pytest.mark.parametrize(
    "param",
    [
        {CONF_FROM: "05:00:00", CONF_TO: "10:00:00"},
        {CONF_FROM: "10:00:00", CONF_TO: "05:00:00", CONF_DISABLED: True},
        {CONF_FROM: "05:00:00", CONF_TO: "05:00:00"},
    ],
    ids=[
        "regular",
        "cross day",
        "entire day",
    ],
)
def test_time_range_to_dict(hass: HomeAssistant, param: dict[str, Any]) -> None:
    """Test TimeRange to_dict."""
    assert (
        TimeRangeConfig(
            hass, param[CONF_FROM], param[CONF_TO], param.get(CONF_DISABLED, False)
        ).to_dict()
        == param
    )


@pytest.mark.parametrize(
    ("schedule", "skip_reversed", "time", "result"),
    [
        ([], False, "05:00", False),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], False, "05:00", True),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], False, "10:00", False),
        (
            [
                {CONF_FROM: "22:00", CONF_TO: "00:00"},
                {CONF_FROM: "05:00", CONF_TO: "10:00"},
            ],
            False,
            "23:00",
            True,
        ),
        (
            [{CONF_FROM: "00:00", CONF_TO: "00:00", CONF_DISABLED: True}],
            False,
            "12:00",
            False,
        ),
        (
            [{CONF_FROM: "00:00", CONF_TO: "00:00"}],
            True,
            "12:00",
            False,
        ),
    ],
    ids=[
        "empty",
        "contained",
        "not contained",
        "2 ranges contained",
        "disabled range",
        "skip reversed",
    ],
)
def test_schedule_containing(
    hass: HomeAssistant,
    schedule: list[dict[str, Any]],
    skip_reversed: bool,  # noqa: FBT001
    time: str,
    result: bool,  # noqa: FBT001
) -> None:
    """Test containing method of Schedule."""
    assert (
        Schedule(hass, schedule, skip_reversed).containing(
            datetime.time.fromisoformat(time)
        )
        is result
    )


@pytest.mark.parametrize(
    ("schedule", "skip_reversed", "on", "off"),
    [
        (
            [
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "07:08:09",
                },
                {
                    CONF_FROM: "10:11:12",
                    CONF_TO: "10:11:13",
                },
            ],
            False,
            "05:06:07",
            None,
        ),
        (
            [
                {
                    CONF_FROM: "04:05:06",
                    CONF_TO: "01:02:03",
                },
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "10:11:12",
                },
            ],
            False,
            "01:00:00",
            "03:00:00",
        ),
        (
            [
                {
                    CONF_FROM: "04:05:05",
                    CONF_TO: "07:08:09",
                },
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
            ],
            False,
            "02:00:00",
            "08:00:00",
        ),
        (
            [
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "01:02:04",
                },
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
            ],
            False,
            "00:00:00",
            "05:00:00",
        ),
        (
            [
                {
                    CONF_FROM: SUNRISE_SYMBOL,
                    CONF_TO: "00:00:00",
                },
            ],
            False,
            "20:00:00",
            "00:00:00",
        ),
        (
            [
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "01:02:04",
                },
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
            ],
            True,
            "02:00:00",
            "00:00:00",
        ),
    ],
    ids=[
        "wrap whole",
        "warp",
        "overlap",
        "overnight_overlap",
        "sunrise to midnight",
        "skip_reversed",
    ],
)
def test_complex_schedule(
    hass: HomeAssistant,
    schedule: list[dict[str, Any]],
    skip_reversed: bool,  # noqa: FBT001
    on: str | None,
    off: str | None,
) -> None:
    """Test complex schedule."""
    test = Schedule(hass, schedule, skip_reversed)
    if on is not None:
        assert test.containing(datetime.time.fromisoformat(on)) is True
    if off is not None:
        assert test.containing(datetime.time.fromisoformat(off)) is False


@pytest.mark.parametrize(
    "schedule",
    [
        [
            {
                CONF_FROM: "01:00:00",
                CONF_TO: "02:00:00",
            },
        ],
        [
            {
                CONF_FROM: "03:00:00",
                CONF_TO: "04:00:00",
                CONF_DISABLED: True,
            },
            {
                CONF_FROM: "01:00:00",
                CONF_TO: "02:00:00",
            },
        ],
    ],
    ids=["one", "two"],
)
def test_to_list(hass: HomeAssistant, schedule: list[dict[str, Any]]) -> None:
    """Test schedule to string list function."""
    str_list = Schedule(hass, schedule, skip_reversed=False).to_list()
    schedule.sort(key=lambda time_range: time_range[CONF_FROM])
    assert str_list == schedule


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        (
            [],
            [],
        ),
        (
            [
                {CONF_FROM: "22:00:00", CONF_TO: "02:00:00"},
                {CONF_FROM: "19:00:00", CONF_TO: "22:00:00"},
            ],
            [{CONF_FROM: "19:00:00", CONF_TO: "02:00:00"}],
        ),
        (
            [
                {CONF_FROM: "01:00:00", CONF_TO: "05:00:00"},
                {CONF_FROM: "23:00:00", CONF_TO: "01:00:00"},
                {CONF_FROM: "05:00:00", CONF_TO: "23:00:00"},
            ],
            [{CONF_FROM: "00:00:00", CONF_TO: "00:00:00"}],
        ),
        (
            [{CONF_FROM: "12:00:00", CONF_TO: "12:00:00"}],
            [{CONF_FROM: "12:00:00", CONF_TO: "12:00:00"}],
        ),
    ],
    ids=["empty", "adjusting", "whole day", "single range"],
)
def test_merge(
    hass: HomeAssistant, schedule: list[dict[str, Any]], expected: list[dict[str, Any]]
) -> None:
    """Test merging logic."""
    assert Schedule(hass, schedule, skip_reversed=False).to_list_absolute() == expected


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        (
            [],
            False,
        ),
        (
            [
                {CONF_FROM: "22:00:00", CONF_TO: "02:00:00"},
            ],
            False,
        ),
        (
            [
                {CONF_FROM: "22:00:00", CONF_TO: "02:00:00"},
                {CONF_FROM: SUNRISE_SYMBOL, CONF_TO: "08:00:00"},
            ],
            True,
        ),
        (
            [
                {CONF_FROM: "22:00:00", CONF_TO: "02:00:00"},
                {CONF_FROM: "12:00:00", CONF_TO: SUNSET_SYMBOL},
            ],
            True,
        ),
    ],
    ids=["empty", "fixed", "dynamic from", "dynamic to"],
)
def test_dynamic(
    hass: HomeAssistant,
    schedule: list[dict[str, Any]],
    expected: bool,  # noqa: FBT001
) -> None:
    """Test is_dynamic logic."""
    assert Schedule(hass, schedule, skip_reversed=False).is_dynamic() == expected


@pytest.mark.parametrize(
    ("schedule", "next_update_sec_offset"),
    [
        ([(-5, 5, False)], 5),
        ([(-10, -5, False)], datetime.timedelta(days=1).total_seconds() - 10),
        ([(5, 10, False)], 5),
        ([(0, 0, False)], None),
        ([(100, 200, False), (200, 100, False)], None),
        ([(-100, 100, False), (100, 200, False)], 200),
        ([(-100, 100, True), (100, 200, False)], 100),
        ([(80, 100, False), (70, 90, False), (0, 80, False)], 100),
        ([(200, 50, False), (20, 100, False)], 100),
    ],
    ids=[
        "inside range",
        "after all ranges",
        "before all ranges",
        "entire_day_1_range",
        "entire_day_2_ranges",
        "adjusted_ranges",
        "disabled_range",
        "overlapping_ranges",
        "overlap_and_wrap",
    ],
)
def test_next_update(
    hass: HomeAssistant,
    schedule: list[Any],
    next_update_sec_offset: int | None,
) -> None:
    """Test next update logic."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
        hass,
        [
            {
                CONF_FROM: (now + datetime.timedelta(seconds=from_sec_offset))
                .time()
                .isoformat(),
                CONF_TO: (now + datetime.timedelta(seconds=to_sec_offset))
                .time()
                .isoformat(),
                CONF_DISABLED: disabled,
            }
            for (from_sec_offset, to_sec_offset, disabled) in schedule
        ],
        skip_reversed=False,
    ).next_update(now) == (
        now + datetime.timedelta(seconds=next_update_sec_offset)
        if next_update_sec_offset is not None
        else None
    )


def test_next_updates(
    hass: HomeAssistant,
) -> None:
    """Test next updates."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
        hass,
        [
            {
                CONF_FROM: "01:00",
                CONF_TO: "02:00",
            },
            {
                CONF_FROM: "03:00",
                CONF_TO: "04:00",
            },
        ],
        skip_reversed=False,
    ).next_updates(now, 5) == [
        now + datetime.timedelta(hours=1),
        now + datetime.timedelta(hours=2),
        now + datetime.timedelta(hours=3),
        now + datetime.timedelta(hours=4),
        now + datetime.timedelta(days=1, hours=1),
    ]


def test_sort_off_timestamps(
    hass: HomeAssistant,
) -> None:
    """Test off calculation correctness when off timestamps requires sorting."""
    now = datetime.datetime.fromisoformat("2000-01-01 22:00")
    assert Schedule(
        hass,
        [
            {
                CONF_FROM: "21:00",
                CONF_TO: "11:00",
            },
            {
                CONF_FROM: "14:00",
                CONF_TO: "16:00",
            },
        ],
        skip_reversed=False,
    ).next_update(now) == now + datetime.timedelta(hours=13)
