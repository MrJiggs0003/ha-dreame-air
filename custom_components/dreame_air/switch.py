"""On/off settings: key-press beep and child lock."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry
from .entity import DreameAirEntity, reports_value

PARALLEL_UPDATES = 1

SWITCHES = ("key_tone", "child_lock")


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add a switch for each writable on/off setting the profile has."""
    coordinator = entry.runtime_data
    profile = coordinator.device.profile
    if not profile.controllable:
        return
    async_add_entities(
        DreameAirSwitch(coordinator, key)
        for key in SWITCHES
        if (prop := profile.prop(key)) and prop.writable and reports_value(coordinator, key)
    )


class DreameAirSwitch(DreameAirEntity, SwitchEntity):
    """One on/off setting."""

    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return bool(self.raw_value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self._key, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self._key, 0)
