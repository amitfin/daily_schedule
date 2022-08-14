"""Support for representing daily schedule as binary sensors."""
from __future__ import annotations

import datetime
from typing import Any
import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import event as event_helper, entity_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import CONF_FROM, CONF_SCHEDULE, CONF_TO, SERVICE_SET
from .schedule import Schedule


def remove_micros_and_tz(time: datetime.time) -> str:
    """Remove microseconds and timezone from a time object."""
    return time.replace(microsecond=0, tzinfo=None).isoformat()


ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FROM): vol.All(cv.time, remove_micros_and_tz),
        vol.Required(CONF_TO): vol.All(cv.time, remove_micros_and_tz),
    },
    extra=vol.ALLOW_EXTRA,
)
SERVICE_SET_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCHEDULE): vol.All(cv.ensure_list, [ENTRY_SCHEMA]),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    async_add_entities([DailyScheduleSenosr(config_entry)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(SERVICE_SET, SERVICE_SET_SCHEMA, "async_set")


class DailyScheduleSenosr(BinarySensorEntity):
    """Representation of a daily schedule sensor."""

    _attr_icon = "mdi:timetable"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize object with defaults."""
        self._config_entry = config_entry
        self._attr_name = config_entry.title
        self._attr_unique_id = config_entry.entry_id
        self._schedule: Schedule = Schedule(config_entry.options.get(CONF_SCHEDULE, []))
        self._unsub_update: CALLBACK_TYPE | None = None

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def is_on(self) -> bool:
        """Return True is sensor is on."""
        return self._schedule.containing(dt_util.now().time())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            CONF_SCHEDULE: self._schedule.to_list(),
        }

    @callback
    def _clean_up_listener(self):
        """Remove the update timer."""
        if self._unsub_update is not None:
            self._unsub_update()
            self._unsub_update = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(self._clean_up_listener)
        self._update_state()

    async def async_set(self, schedule: list[dict[str, str]]) -> None:
        """Update the config entry with the new list. Required for non-admin use cases."""
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options={CONF_SCHEDULE: Schedule(schedule).to_list()},
        )

    def _schedule_update(self) -> None:
        """Schedule a timer for the point when the state should be changed."""
        self._clean_up_listener()

        next_update = self._schedule.next_update(dt_util.now())
        if not next_update:
            return

        self._unsub_update = event_helper.async_track_point_in_time(
            self.hass, self._update_state, next_update
        )

    @callback
    def _update_state(self, *_):
        """Update the state to reflect the current time."""
        self._schedule_update()
        self.async_write_ha_state()
