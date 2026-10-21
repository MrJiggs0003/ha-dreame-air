"""Shared fixtures: a fake Dreame cloud that records every command."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dreame_air.const import CONF_DID, CONF_HOST, CONF_MAC, CONF_MODEL, CONF_REGION, DOMAIN

DID = "123456789"
FP10_MODEL = "dreame.airp.u2513"

# A plausible FP10 in Smart mode at speed 5.
FP10_VALUES: dict[tuple[int, int], Any] = {
    (1, 4): "2062",
    (1, 5): "U2513TEST",
    (2, 1): 1,
    (2, 3): 0,
    (2, 4): 5,
    (3, 2): 54,
    (3, 3): 22,
    (3, 4): 1,
    (3, 5): 8,
    (3, 9): 14,
    (3, 12): 8,  # the display's number; must not be read as PM2.5
    (4, 1): 98,
    (4, 2): 709,
    (4, 3): 120,
    (4, 5): 100,
    (6, 5): "",
    (6, 6): 50,
    (6, 8): 0,
    (6, 12): 0,
    (6, 17): 1,
}


def device_record(model: str = FP10_MODEL, did: str = DID, name: str = "Bedroom Purifier") -> dict[str, Any]:
    return {
        "did": did,
        "model": model,
        "customName": name,
        "bindDomain": "10000.mt.us.iot.dreame.tech:19973",
        "mac": "AA:BB:CC:DD:EE:FF",
    }


class FakeCloud:
    """Stands in for DreameCloud. Power toggles like the real FP10."""

    def __init__(self) -> None:
        self.devices: list[dict[str, Any]] = [device_record()]
        self.values: dict[tuple[int, int], Any] = dict(FP10_VALUES)
        self.calls: list[tuple[Any, ...]] = []
        self.login_error: Exception | None = None
        self.read_error: Exception | None = None

    async def login(self) -> None:
        if self.login_error:
            raise self.login_error

    async def get_devices(self) -> list[dict[str, Any]]:
        await self.login()
        return self.devices

    async def get_properties(
        self, did: str, host: str | None, addresses: list[tuple[int, int]]
    ) -> dict[tuple[int, int], Any]:
        if self.read_error:
            raise self.read_error
        self.calls.append(("get", tuple(addresses)))
        return {a: self.values[a] for a in addresses if a in self.values}

    async def set_property(self, did: str, host: str | None, siid: int, piid: int, value: Any) -> None:
        self.calls.append(("set", siid, piid, value))
        self.values[(siid, piid)] = value

    async def call_action(self, did: str, host: str | None, siid: int, aiid: int) -> None:
        self.calls.append(("action", siid, aiid))
        if (siid, aiid) == (2, 3):
            self.values[(2, 1)] = 2 if self.values.get((2, 1)) == 1 else 1

    @property
    def writes(self) -> list[tuple[Any, ...]]:
        return [c for c in self.calls if c[0] != "get"]

    @property
    def addresses_read(self) -> set[tuple[int, int]]:
        return {a for c in self.calls if c[0] == "get" for a in c[1]}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load custom_components/dreame_air."""


@pytest.fixture
def cloud() -> FakeCloud:
    fake = FakeCloud()
    with (
        patch("custom_components.dreame_air.DreameCloud", return_value=fake),
        patch("custom_components.dreame_air.config_flow.DreameCloud", return_value=fake),
    ):
        yield fake


def make_entry(model: str = FP10_MODEL, options: dict[str, Any] | None = None) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom Purifier",
        unique_id=DID,
        data={
            "username": "user@example.com",
            "password": "secret",
            CONF_REGION: "us",
            CONF_DID: DID,
            CONF_MODEL: model,
            CONF_HOST: "10000.mt.us.iot.dreame.tech:19973",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        options=options or {},
    )
