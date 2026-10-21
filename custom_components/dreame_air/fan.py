"""The purifier itself, as a fan entity."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.percentage import percentage_to_ranged_value, ranged_value_to_percentage

from .const import CONF_OFF_BEHAVIOR, DEFAULT_OFF_BEHAVIOR, OFF_REAL
from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .device import POWER_ON
from .entity import DreameAirEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add the fan if the profile allows control."""
    coordinator = entry.runtime_data
    if coordinator.device.profile.has_fan:
        async_add_entities([DreameAirFan(coordinator)])


class DreameAirFan(DreameAirEntity, FanEntity):
    """On/off, speed and preset modes.

    With soft off (the default), "off" means the profile's quietest state, so the
    purifier stays reachable: some models can't be woken remotely once powered off.
    """

    _attr_name = None

    def __init__(self, coordinator: DreameAirCoordinator) -> None:
        super().__init__(coordinator, "power")
        self._attr_translation_key = "purifier"
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_fan"
        self._attr_preset_modes = list(self.profile.modes.values())
        self._attr_speed_count = self.profile.speed_count
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )
        self._speed_range = (1, self.profile.speed_count)

    @property
    def _powered(self) -> bool:
        return self.data.get("power") == POWER_ON

    @property
    def is_on(self) -> bool:
        return self._powered and not self.device.is_soft_off(self.data)

    @property
    def percentage(self) -> int | None:
        speed = self.data.get("fan_speed")
        if not self.is_on or not speed:
            return 0
        return ranged_value_to_percentage(self._speed_range, speed)

    @property
    def preset_mode(self) -> str | None:
        if not self.is_on:
            return None
        return self.profile.modes.get(self.data.get("mode"))

    def _mode_for(self, preset_mode: str) -> int:
        return next(value for value, name in self.profile.modes.items() if name == preset_mode)

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        if percentage:
            await self.async_set_percentage(percentage)
            return
        mode = self._mode_for(preset_mode) if preset_mode else None
        await self.coordinator.async_command(self.device.turn_on(self.data, mode))

    async def async_turn_off(self, **kwargs: Any) -> None:
        real = self.coordinator.config_entry.options.get(CONF_OFF_BEHAVIOR, DEFAULT_OFF_BEHAVIOR) == OFF_REAL
        await self.coordinator.async_command(self.device.turn_off(self.data, real))

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        speed = math.ceil(percentage_to_ranged_value(self._speed_range, percentage))
        if not self._powered:
            await self.coordinator.async_command(self.device.turn_on(self.data, self.profile.manual_mode))
        await self.coordinator.async_command(self.device.set_speed(self.data, speed))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.async_command(self.device.turn_on(self.data, self._mode_for(preset_mode)))
