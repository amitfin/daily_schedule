"""The tests for the schedule class."""

from __future__ import annotations

import datetime
from typing import Any

import pytest

from custom_components.daily_schedule.const import CONF_DISABLED, CONF_FROM, CONF_TO
from custom_components.daily_schedule.schedule import Schedule, TimeRange


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
def test_time_range(
    start: str,
    end: str,
    time: str,
    disabled: bool,  # noqa: FBT001
    result: bool,  # noqa: FBT001
) -> None:
    """Test for TimeRange class."""
    assert (
        TimeRange(start, end, disabled).containing(datetime.time.fromisoformat(time))
        is result
    )


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
def test_time_range_to_dict(param: dict[str, Any]) -> None:
    """Test TimeRange to_dict."""
    assert (
        TimeRange(
            param[CONF_FROM], param[CONF_TO], param.get(CONF_DISABLED, False)
        ).to_dict()
        == param
    )


@pytest.mark.parametrize(
    ("schedule", "time", "result"),
    [
        ([], "05:00", False),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], "05:00", True),
        ([{CONF_FROM: "05:00", CONF_TO: "10:00"}], "10:00", False),
        (
            [
                {CONF_FROM: "22:00", CONF_TO: "00:00"},
                {CONF_FROM: "05:00", CONF_TO: "10:00"},
            ],
            "23:00",
            True,
        ),
        ([{CONF_FROM: "00:00", CONF_TO: "00:00", CONF_DISABLED: True}], "12:00", False),
    ],
    ids=[
        "empty",
        "contained",
        "not contained",
        "2 ranges contained",
        "disabled range",
    ],
)
def test_schedule_containing(
    schedule: list[dict[str, Any]],
    time: str,
    result: bool,  # noqa: FBT001
) -> None:
    """Test containing method of Schedule."""
    assert Schedule(schedule).containing(datetime.time.fromisoformat(time)) is result


@pytest.mark.parametrize(
    ("schedule", "reason"),
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
                    CONF_DISABLED: True,
                },
                {
                    CONF_FROM: "10:11:12",
                    CONF_TO: "10:11:13",
                },
            ],
            "zero",
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
            "negative",
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
                    CONF_DISABLED: True,
                },
            ],
            "overlap",
        ),
        (
            [
                {
                    CONF_FROM: "07:08:09",
                    CONF_TO: "01:02:04",
                    CONF_DISABLED: True,
                },
                {
                    CONF_FROM: "01:02:03",
                    CONF_TO: "04:05:06",
                },
            ],
            "overlap",
        ),
    ],
    ids=["zero length", "negative length", "overlap", "overnight_overlap"],
)
def test_invalid(schedule: list[dict[str, Any]], reason: str) -> None:
    """Test invalid schedule."""
    with pytest.raises(ValueError) as excinfo:  # noqa: PT011
        Schedule(schedule)
    assert reason in str(excinfo.value)


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
def test_to_list(schedule: list[dict[str, Any]]) -> None:
    """Test schedule to string list function."""
    str_list = Schedule(schedule).to_list()
    schedule.sort(key=lambda time_range: time_range[CONF_FROM])
    assert str_list == schedule


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
    ],
    ids=[
        "inside range",
        "after all ranges",
        "before all ranges",
        "entire_day_1_range",
        "entire_day_2_ranges",
        "adjusted_ranges",
        "disabled_range",
    ],
)
def test_next_update(
    schedule: list[Any],
    next_update_sec_offset: int | None,
) -> None:
    """Test next update logic."""
    now = datetime.datetime.fromisoformat("2000-01-01")
    assert Schedule(
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
        ]
    ).next_update(now) == (
        now + datetime.timedelta(seconds=next_update_sec_offset)
        if next_update_sec_offset is not None
        else None
    )
