"""Air quality, environment and filter sensors."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DreameAirConfigEntry, DreameAirCoordinator

try:
    from homeassistant.const import UnitOfDensity

    _UG = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER
    _MG = UnitOfDensity.MILLIGRAMS_PER_CUBIC_METER
except ImportError:  # Home Assistant before UnitOfDensity existed
    from homeassistant.const import (
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER as _UG,
        CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER as _MG,
    )
from .entity import DreameAirEntity

PARALLEL_UPDATES = 0

_M = SensorStateClass.MEASUREMENT
_D = EntityCategory.DIAGNOSTIC


@dataclass(frozen=True, kw_only=True)
class DreameAirSensorDescription(SensorEntityDescription):
    """A sensor for one profile property."""

    # Only shown when the property can't be controlled through another entity.
    read_only_only: bool = False


SENSORS: tuple[DreameAirSensorDescription, ...] = (
    DreameAirSensorDescription(
        key="pm25", device_class=SensorDeviceClass.PM25, native_unit_of_measurement=_UG, state_class=_M
    ),
    DreameAirSensorDescription(
        key="pm10", device_class=SensorDeviceClass.PM10, native_unit_of_measurement=_UG, state_class=_M
    ),
    DreameAirSensorDescription(
        key="pm1", device_class=SensorDeviceClass.PM1, native_unit_of_measurement=_UG, state_class=_M
    ),
    DreameAirSensorDescription(
        key="tvoc",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        native_unit_of_measurement=_UG,
        state_class=_M,
    ),
    DreameAirSensorDescription(
        key="hcho",
        native_unit_of_measurement=_MG,
        state_class=_M,
        suggested_display_precision=3,
    ),
    DreameAirSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=_M,
    ),
    DreameAirSensorDescription(
        key="humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=_M
    ),
    DreameAirSensorDescription(key="air_quality_level", state_class=_M),
    DreameAirSensorDescription(key="filter_life", native_unit_of_measurement=PERCENTAGE, state_class=_M),
    DreameAirSensorDescription(
        key="filter_days_left", device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.DAYS
    ),
    DreameAirSensorDescription(
        key="filter_hours_used",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=_D,
    ),
    DreameAirSensorDescription(key="hair_box_life", native_unit_of_measurement=PERCENTAGE, state_class=_M),
    DreameAirSensorDescription(key="carbon_filter_life", native_unit_of_measurement=PERCENTAGE, state_class=_M),
    DreameAirSensorDescription(
        key="carbon_filter_days_left",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    DreameAirSensorDescription(
        key="carbon_filter_hours_used",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=_D,
    ),
    DreameAirSensorDescription(key="mode", read_only_only=True),
    DreameAirSensorDescription(key="fan_speed", state_class=_M, read_only_only=True),
    DreameAirSensorDescription(
        key="off_timer",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        read_only_only=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: DreameAirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add a sensor for each property the profile reads."""
    coordinator = entry.runtime_data
    profile = coordinator.device.profile
    async_add_entities(
        DreameAirSensor(coordinator, description)
        for description in SENSORS
        if (prop := profile.prop(description.key)) is not None
        and prop.address not in profile.unsafe_reads
        and not (description.read_only_only and profile.controllable)
    )


class DreameAirSensor(DreameAirEntity, SensorEntity):
    """One property as a sensor."""

    entity_description: DreameAirSensorDescription

    def __init__(self, coordinator: DreameAirCoordinator, description: DreameAirSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        options = self.profile.prop(description.key).options  # type: ignore[union-attr]
        if options:
            # Enum-like property: show the named level, not the number.
            self._options = options
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(options.values())
            self._attr_state_class = None
        else:
            self._options = None

    @property
    def native_value(self) -> str | int | float | None:
        value = self.value
        if self._options is not None:
            return self._options.get(value)
        return value if isinstance(value, (int, float)) else None
