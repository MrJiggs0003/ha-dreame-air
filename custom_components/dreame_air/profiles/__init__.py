"""Model profiles: what each Dreame purifier can safely be asked to do.

A profile is pure data. The device layer (device.py) refuses any read, write or
action that the device's profile doesn't declare, so a wrong guess about one
model can't reach another. Some models crash on commands that are correct for
others: the TP20 goes offline on the power toggle that the FP10 and PM10 use.

To add a model, add a module here with a PROFILE and list it in _PROFILES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Status(StrEnum):
    """How much of a profile has been confirmed on a real device."""

    VERIFIED = "verified"  # tested end to end by this project
    COMMUNITY = "community"  # mapped by other owners; not tested here
    READ_ONLY = "read_only"  # sensors only; nothing is ever written


@dataclass(frozen=True, slots=True)
class Prop:
    """One MIoT property.

    values: allowed write values; None means the property is read-only.
    options: value -> option key, for enum-like properties (translated).
    scale: multiplier applied to the raw value when reading.
    needs_value: only create the entity if the device reports a real value.
    """

    key: str
    siid: int
    piid: int
    values: frozenset[int] | None = None
    options: dict[int, str] | None = None
    scale: float = 1.0
    needs_value: bool = False

    @property
    def address(self) -> tuple[int, int]:
        return (self.siid, self.piid)

    @property
    def writable(self) -> bool:
        return self.values is not None


@dataclass(frozen=True, slots=True)
class Action:
    """One MIoT action, called without parameters."""

    key: str
    siid: int
    aiid: int

    @property
    def address(self) -> tuple[int, int]:
        return (self.siid, self.aiid)


@dataclass(frozen=True, slots=True)
class Profile:
    """Everything the integration may do with one model.

    power_action: key of the action that toggles power, or None when the model
        has no known safe way to switch power remotely.
    modes: mode value -> preset key. manual_mode is the mode in which the fan
        speed can be set.
    soft_off: writes, in order, that put the purifier in its quietest state.
        Some models can't be woken remotely once fully powered off.
    on_mode: mode set when turning on without a preset.
    """

    model: str
    name: str
    status: Status
    props: tuple[Prop, ...]
    actions: tuple[Action, ...] = ()
    power_action: str | None = None
    modes: dict[int, str] = field(default_factory=dict)
    manual_mode: int | None = None
    on_mode: int | None = None
    speed_count: int = 0
    soft_off: tuple[tuple[str, int], ...] = ()
    unsafe_reads: frozenset[tuple[int, int]] = frozenset()
    unsafe_actions: frozenset[tuple[int, int]] = frozenset()

    def prop(self, key: str) -> Prop | None:
        return next((p for p in self.props if p.key == key), None)

    def action(self, key: str) -> Action | None:
        return next((a for a in self.actions if a.key == key), None)

    @property
    def readable(self) -> tuple[Prop, ...]:
        return tuple(p for p in self.props if p.address not in self.unsafe_reads)

    @property
    def controllable(self) -> bool:
        return self.status is not Status.READ_ONLY

    @property
    def has_fan(self) -> bool:
        return self.controllable and bool(self.modes) and all(self.prop(k) for k in ("power", "mode", "fan_speed"))


def speeds(count: int) -> frozenset[int]:
    return frozenset(range(1, count + 1))


def value_range(low: int, high: int) -> frozenset[int]:
    return frozenset(range(low, high + 1))


ON_OFF = frozenset({0, 1})


def all_profiles() -> list[Profile]:
    """Return every known profile."""
    # Imported here: the model modules import the dataclasses above.
    from . import ap10, fp10, pm10, pm20, tp20

    return [fp10.PROFILE, ap10.PROFILE, pm10.PROFILE, tp20.PROFILE, pm20.PROFILE]


def get_profile(model: str) -> Profile | None:
    """Return the profile for a model ID, or None if it isn't supported."""
    return next((p for p in all_profiles() if p.model == model), None)


__all__ = ["ON_OFF", "Action", "Profile", "Prop", "Status", "all_profiles", "get_profile", "speeds", "value_range"]
