"""Filter replacement warning."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import FILTER_DAYS_THRESHOLD, FILTER_LIFE_THRESHOLD
from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .entity import DreameAirEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add the warning if the profile reports filter life."""
    coordinator = entry.runtime_data
    if coordinator.device.profile.prop("filter_life"):
        async_add_entities([DreameAirFilterWarning(coordinator)])


class DreameAirFilterWarning(DreameAirEntity, BinarySensorEntity):
    """On when the main filter is due for replacement."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: DreameAirCoordinator) -> None:
        super().__init__(coordinator, "filter_life")
        self._attr_translation_key = "filter_replacement"
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_filter_replacement"

    @property
    def is_on(self) -> bool | None:
        life = self.data.get("filter_life")
        days = self.data.get("filter_days_left")
        if not isinstance(life, (int, float)):
            return None
        return life <= FILTER_LIFE_THRESHOLD or (isinstance(days, (int, float)) and days <= FILTER_DAYS_THRESHOLD)
