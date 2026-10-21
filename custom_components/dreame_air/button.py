"""Filter reset buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry, DreameAirCoordinator
from .entity import DreameAirEntity

PARALLEL_UPDATES = 1

# action key -> property the reset affects (decides availability)
BUTTONS = {"reset_filter": "filter_life", "reset_carbon_filter": "carbon_filter_life"}


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add a button for each reset action the profile allows."""
    coordinator = entry.runtime_data
    profile = coordinator.device.profile
    if not profile.controllable:
        return
    async_add_entities(
        DreameAirResetButton(coordinator, action, prop)
        for action, prop in BUTTONS.items()
        if (found := profile.action(action)) and found.address not in profile.unsafe_actions
    )


class DreameAirResetButton(DreameAirEntity, ButtonEntity):
    """Tell the purifier its filter was replaced."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: DreameAirCoordinator, action: str, prop: str) -> None:
        super().__init__(coordinator, prop)
        self._action = action
        self._attr_translation_key = action
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{action}"

    async def async_press(self) -> None:
        await self.coordinator.async_command(self.device.run(self._action))
