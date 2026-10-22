"""The purifier's display light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_EFFECT, ColorMode, LightEntity, LightEntityFeature
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .entity import DreameAirEntity

PARALLEL_UPDATES = 1

EFFECT_STEADY = "steady"
EFFECT_BREATHING = "breathing"
DEFAULT_BRIGHTNESS = 50  # device value, used when turned on without a brightness


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add the display light if the profile can dim it."""
    coordinator = entry.runtime_data
    prop = coordinator.device.profile.prop("display_brightness")
    if coordinator.device.profile.controllable and prop and prop.writable:
        async_add_entities([DreameAirDisplayLight(coordinator)])


class DreameAirDisplayLight(DreameAirEntity, LightEntity):
    """Display brightness, plus a breathing effect where supported.

    Home Assistant's full brightness maps to the profile's highest allowed value
    (80 on the FP10), so the whole slider is usable.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: DreameAirCoordinator) -> None:
        super().__init__(coordinator, "display_brightness")
        self._attr_translation_key = "display"
        self._breathing = coordinator.device.profile.prop("display_breathing") is not None
        if self._breathing:
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = [EFFECT_STEADY, EFFECT_BREATHING]
        self._max = max(coordinator.device.profile.prop("display_brightness").values)  # type: ignore[union-attr, arg-type]
        self._last_on = min(DEFAULT_BRIGHTNESS, self._max)

    @property
    def is_on(self) -> bool:
        return bool(self.raw_value)

    @property
    def brightness(self) -> int | None:
        if not self.raw_value:
            return None
        return min(255, round(int(self.raw_value) * 255 / self._max))

    @property
    def effect(self) -> str | None:
        if not self._breathing:
            return None
        return EFFECT_BREATHING if self.data.get("display_breathing") else EFFECT_STEADY

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_EFFECT in kwargs and self._breathing:
            await self.coordinator.async_write("display_breathing", int(kwargs[ATTR_EFFECT] == EFFECT_BREATHING))
        if ATTR_BRIGHTNESS in kwargs:
            level = max(1, round(kwargs[ATTR_BRIGHTNESS] * self._max / 255))
        elif self.is_on and ATTR_EFFECT in kwargs:
            return
        else:
            level = self._last_on
        await self.coordinator.async_write("display_brightness", level)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.raw_value:
            self._last_on = int(self.raw_value)
        await self.coordinator.async_write("display_brightness", 0)
