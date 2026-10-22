"""Base entity for Dreame Air."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, MANUFACTURER
from .coordinator import DreameAirCoordinator
from .device import DreameDevice
from .profiles import Profile


class DreameAirEntity(CoordinatorEntity[DreameAirCoordinator]):
    """An entity backed by one or more of the purifier's properties.

    key is the profile property the entity reads; the entity is unavailable
    while the device isn't reporting it.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: DreameAirCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        profile = coordinator.device.profile
        data = coordinator.data or {}
        mac = entry.data.get(CONF_MAC)
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            connections={(CONNECTION_NETWORK_MAC, format_mac(mac))} if mac else set(),
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=profile.name,
            model_id=profile.model,
            sw_version=str(data["firmware"]) if data.get("firmware") else None,
            serial_number=str(data["serial"]) if data.get("serial") else None,
        )

    @property
    def device(self) -> DreameDevice:
        return self.coordinator.device

    @property
    def profile(self) -> Profile:
        return self.coordinator.device.profile

    @property
    def data(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def raw_value(self) -> Any:
        # Not "value": NumberEntity.value is final and converts units.
        return self.data.get(self._key)

    @property
    def available(self) -> bool:
        return super().available and self._key in self.data


def reports_value(coordinator: DreameAirCoordinator, key: str) -> bool:
    """Whether to create an entity for a property marked needs_value."""
    prop = coordinator.device.profile.prop(key)
    if prop is None:
        return False
    if not prop.needs_value:
        return True
    return (coordinator.data or {}).get(key) not in (None, "")
