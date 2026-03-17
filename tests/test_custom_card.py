"""The tests for the custom_card file."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daily_schedule.const import DOMAIN
from custom_components.daily_schedule.custom_card import CARD_FILE, FRONTEND_PATH

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_setup_js_url(hass: HomeAssistant) -> None:
    """Test setup registers extra JS URL with a deterministic cache-busting value."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.daily_schedule.custom_card.add_extra_js_url"
        ) as mock_add_extra_js_url,
        patch(
            "custom_components.daily_schedule.custom_card.async_get_integration",
            new=AsyncMock(return_value=SimpleNamespace(version="2.3.4")),
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

    mock_add_extra_js_url.assert_called_once_with(
        hass, "/daily_schedule_internal_static/daily-schedule-card.js?v=2.3.4"
    )


def test_card_file_exists() -> None:
    """Verify that the card file exists."""
    assert (Path(FRONTEND_PATH) / CARD_FILE).is_file()
