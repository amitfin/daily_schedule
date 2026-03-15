"""Publish JS custom card."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Final

import homeassistant.util.dt as dt_util
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.loader import async_get_integration

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

FRONTEND_PATH: Final = Path(__file__).parent / "cards"
CARD_FILE: Final = "daily-schedule-card.js"
URL_BASE: Final = f"/{DOMAIN}_internal_static"


async def publish_card(hass: HomeAssistant) -> None:
    """Publish the custom card."""
    _, integration = await asyncio.gather(
        hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(FRONTEND_PATH), cache_headers=True)]
        ),
        async_get_integration(hass, DOMAIN),
    )

    if integration.version and integration.version != "1.0.0":
        version = str(integration.version)
    else:
        version = str(int(dt_util.now().timestamp()))

    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={version}")
