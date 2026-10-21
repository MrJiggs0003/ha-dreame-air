"""Settings with named options, such as the AP10's light color."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .entity import DreameAirEntity

PARALLEL_UPDATES = 1

# Properties handled by other platforms, even though they have named values.
_EXCLUDED = {"mode", "air_quality_level"}


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add a select for each writable property with named options."""
    coordinator = entry.runtime_data
    profile = coordinator.device.profile
    if not profile.controllable:
        return
    async_add_entities(
        DreameAirSelect(coordinator, prop.key)
        for prop in profile.props
        if prop.writable and prop.options and prop.key not in _EXCLUDED
    )


class DreameAirSelect(DreameAirEntity, SelectEntity):
    """One setting with named options."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: DreameAirCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._values = coordinator.device.profile.prop(key).options  # type: ignore[union-attr]
        self._attr_options = list(self._values.values())  # type: ignore[union-attr]

    @property
    def current_option(self) -> str | None:
        return self._values.get(self.value)  # type: ignore[union-attr]

    async def async_select_option(self, option: str) -> None:
        value = next(v for v, name in self._values.items() if name == option)  # type: ignore[union-attr]
        await self.coordinator.async_write(self._key, value)
