"""Off timer."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .entity import DreameAirEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add the timer if the profile can set it."""
    coordinator = entry.runtime_data
    prop = coordinator.device.profile.prop("off_timer")
    if coordinator.device.profile.controllable and prop and prop.writable:
        async_add_entities([DreameAirOffTimer(coordinator)])


class DreameAirOffTimer(DreameAirEntity, NumberEntity):
    """Hours until the purifier switches itself off; 0 means no timer."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: DreameAirCoordinator) -> None:
        super().__init__(coordinator, "off_timer")
        values = coordinator.device.profile.prop("off_timer").values  # type: ignore[union-attr]
        self._attr_native_min_value = min(values)  # type: ignore[arg-type]
        self._attr_native_max_value = max(values)  # type: ignore[arg-type]

    @property
    def native_value(self) -> float | None:
        return self.value if isinstance(self.value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write(self._key, int(value))
