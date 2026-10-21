"""One purifier, seen through its profile.

Every read, write and action goes through here, and anything the profile
doesn't declare is refused before it reaches the cloud. Entities never talk to
DreameCloud directly.
"""

from __future__ import annotations

import logging
from typing import Any

from .api import DreameCloud
from .const import READ_BATCH_SIZE
from .profiles import Profile, Status

_LOGGER = logging.getLogger(__name__)

POWER_ON = 1


class NotAllowed(Exception):
    """The profile doesn't allow this command."""


class DreameDevice:
    """Guarded access to one device."""

    def __init__(self, cloud: DreameCloud, profile: Profile, did: str, host: str | None) -> None:
        self.cloud = cloud
        self.profile = profile
        self.did = did
        self.host = host
        if profile.status is Status.COMMUNITY:
            _LOGGER.info(
                "The %s profile hasn't been tested by this integration. Please report what works",
                profile.name,
            )

    # --- guarded primitives ---------------------------------------------

    async def read_all(self) -> dict[str, Any]:
        """Read every safe property in the profile, keyed by property key."""
        props = self.profile.readable
        raw: dict[tuple[int, int], Any] = {}
        for start in range(0, len(props), READ_BATCH_SIZE):
            batch = [p.address for p in props[start : start + READ_BATCH_SIZE]]
            raw.update(await self.cloud.get_properties(self.did, self.host, batch))
        values: dict[str, Any] = {}
        for prop in props:
            if prop.address in raw:
                value = raw[prop.address]
                if prop.scale != 1 and isinstance(value, (int, float)):
                    value = round(value * prop.scale, 3)
                values[prop.key] = value
        return values

    async def write(self, key: str, value: int) -> None:
        """Write a property, if the profile allows that value."""
        prop = self.profile.prop(key)
        if not self.profile.controllable or prop is None or not prop.writable:
            raise NotAllowed(f"{self.profile.name}: {key} can't be written")
        if value not in prop.values:  # type: ignore[operator]
            raise NotAllowed(f"{self.profile.name}: {value} isn't an allowed value for {key}")
        await self.cloud.set_property(self.did, self.host, prop.siid, prop.piid, value)

    async def run(self, key: str) -> None:
        """Run an action, if the profile declares it and it isn't marked unsafe."""
        action = self.profile.action(key)
        if not self.profile.controllable or action is None:
            raise NotAllowed(f"{self.profile.name}: action {key} isn't available")
        if action.address in self.profile.unsafe_actions:
            raise NotAllowed(f"{self.profile.name}: action {key} is unsafe on this model")
        await self.cloud.call_action(self.did, self.host, action.siid, action.aiid)

    # --- purifier operations -------------------------------------------------

    @property
    def can_power(self) -> bool:
        return self.profile.power_action is not None

    def is_soft_off(self, data: dict[str, Any]) -> bool:
        """True when the purifier is in the state soft off leaves it in."""
        return bool(self.profile.soft_off) and all(data.get(k) == v for k, v in self.profile.soft_off)

    async def turn_on(self, data: dict[str, Any], mode: int | None) -> dict[str, Any]:
        """Turn on, optionally in a mode. Returns the values written."""
        written: dict[str, Any] = {}
        if data.get("power") != POWER_ON:
            if not self.can_power:
                raise NotAllowed(
                    f"The {self.profile.name} is in standby and can't be turned on remotely."
                    " Use its power button or the Dreamehome app"
                )
            await self.run(self.profile.power_action)  # type: ignore[arg-type]
            written["power"] = POWER_ON
        target = mode if mode is not None else self.profile.on_mode
        if target is not None and (target != data.get("mode") or self.is_soft_off(data)):
            await self.write("mode", target)
            written["mode"] = target
        return written

    async def turn_off(self, data: dict[str, Any], real: bool) -> dict[str, Any]:
        """Turn off. Soft off keeps it reachable; real off may not be undoable remotely."""
        if real and self.can_power:
            if data.get("power") == POWER_ON:
                await self.run(self.profile.power_action)  # type: ignore[arg-type]
            return {"power": 2}
        if not self.profile.soft_off:
            raise NotAllowed(f"{self.profile.name} has no way to turn off")
        written: dict[str, Any] = {}
        for key, value in self.profile.soft_off:
            await self.write(key, value)
            written[key] = value
        return written

    async def set_speed(self, data: dict[str, Any], speed: int) -> dict[str, Any]:
        """Set a fan speed, switching to the manual mode first when needed."""
        written: dict[str, Any] = {}
        manual = self.profile.manual_mode
        if manual is not None and data.get("mode") != manual:
            await self.write("mode", manual)
            written["mode"] = manual
        await self.write("fan_speed", speed)
        written["fan_speed"] = speed
        return written
