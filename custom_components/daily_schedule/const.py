"""Constants for the Daily Schedule integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "daily_schedule"
LOGGER = logging.getLogger(__package__)

CONF_DISABLED = "disabled"
CONF_FROM: Final = "from"
CONF_TO: Final = "to"
CONF_SCHEDULE: Final = "schedule"
CONF_UTC: Final = "utc"
CONF_SKIP_REVERSED: Final = "skip_reversed"

ATTR_EFFECTIVE_SCHEDULE: Final = "effective_schedule"
ATTR_NEXT_TOGGLE: Final = "next_toggle"
ATTR_NEXT_TOGGLES: Final = "next_toggles"
NEXT_TOGGLES_COUNT: Final = 4

SERVICE_SET: Final = "set"

SUNRISE_SYMBOL: Final = "↑"
SUNSET_SYMBOL: Final = "↓"
