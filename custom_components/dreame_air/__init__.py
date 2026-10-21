"""The Dreame Air integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DreameCloud
from .const import CONF_DID, CONF_HOST, CONF_MODEL, CONF_REGION, DOMAIN
from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .device import DreameDevice
from .profiles import get_profile

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


def _issue_id(entry: DreameAirConfigEntry) -> str:
    return f"unsupported_model_{entry.entry_id}"


async def async_setup_entry(hass: HomeAssistant, entry: DreameAirConfigEntry) -> bool:
    """Set up one purifier."""
    model = entry.data[CONF_MODEL]
    profile = get_profile(model)
    if profile is None:
        # Guessing at commands can crash some models, so unknown ones get no entities.
        ir.async_create_issue(
            hass,
            DOMAIN,
            _issue_id(entry),
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="unsupported_model",
            translation_placeholders={"name": entry.title, "model": model},
        )
        entry.runtime_data = None  # type: ignore[assignment]
        return True

    cloud = DreameCloud(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_REGION],
    )
    device = DreameDevice(cloud, profile, entry.data[CONF_DID], entry.data.get(CONF_HOST))
    coordinator = DreameAirCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: DreameAirConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DreameAirConfigEntry) -> bool:
    """Unload one purifier."""
    if entry.runtime_data is None:
        ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
        return True
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: DreameAirConfigEntry) -> None:
    """Clean up the unsupported-model notice when the entry is deleted."""
    ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
