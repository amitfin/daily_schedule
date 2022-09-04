"""Constants for the Daily Schedule integration."""
import logging
from typing import Final

DOMAIN: Final = "daily_schedule"
LOGGER = logging.getLogger(__package__)

CONF_FROM: Final = "from"
CONF_TO: Final = "to"
CONF_SCHEDULE: Final = "schedule"

ATTR_NEXT_UPDATE: Final = "next_update"

SERVICE_SET: Final = "set"
