"""Shared entity filtering for daily schedule triggers and conditions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class DailyScheduleEntityFilter:
    """Restrict matching to binary sensor entities owned by this integration."""

    _hass: HomeAssistant

    def entity_filter(self, entities: set[str]) -> set[str]:
        """Filter entities to those created by this integration."""
        registry = er.async_get(self._hass)
        return {
            entity_id
            for entity_id in entities
            if (entry := registry.async_get(entity_id)) is not None
            and entry.platform == DOMAIN
            and entry.domain == BINARY_SENSOR_DOMAIN
        }
