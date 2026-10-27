"""The cloud client: login, parsing, and never retrying writes."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.dreame_air.api import AuthFailed, CannotConnect, CommandFailed, DreameCloud

BASE = "https://us.iot.dreame.tech:13267"
TOKEN_URL = f"{BASE}/dreame-auth/oauth/token"
CMD_URL = f"{BASE}/dreame-iot-com-10000/device/sendCommand"
HOST = "10000.mt.us.iot.dreame.tech:19973"
TOKEN = {"access_token": "abc", "refresh_token": "def", "expires_in": 3600}


def _cloud(hass: HomeAssistant) -> DreameCloud:
    return DreameCloud(async_get_clientsession(hass), "user@example.com", "secret", "us")


async def test_login_and_read(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(TOKEN_URL, json=TOKEN)
    aioclient_mock.post(
        CMD_URL,
        json={
            "code": 0,
            "data": {
                "result": [
                    {"siid": 2, "piid": 1, "code": 0, "value": 1},
                    {"siid": 3, "piid": 12, "code": 0, "value": None},
                    {"siid": 6, "piid": 5, "code": -4001},
                ]
            },
        },
    )
    values = await _cloud(hass).get_properties("1", HOST, [(2, 1), (3, 12), (6, 5)])
    assert values == {(2, 1): 1}
    form = aioclient_mock.mock_calls[0][2]
    # Only the salted hash is sent, never the password itself.
    assert form["password"] == hashlib.md5(b"secretRAylYC%fmSKp7%Tq").hexdigest()  # noqa: S324
    assert "secret" not in form.values()


async def test_bad_password(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(TOKEN_URL, status=401, json={"error_description": "Bad credentials"})
    with pytest.raises(AuthFailed):
        await _cloud(hass).login()


async def test_cloud_down(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(TOKEN_URL, exc=TimeoutError())
    with pytest.raises(CannotConnect):
        await _cloud(hass).login()


async def test_write_is_not_retried(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(TOKEN_URL, json=TOKEN)
    aioclient_mock.post(CMD_URL, exc=TimeoutError())
    cloud = _cloud(hass)
    with pytest.raises(CannotConnect):
        await cloud.call_action("1", HOST, 2, 3)
    assert sum(1 for c in aioclient_mock.mock_calls if str(c[1]) == CMD_URL) == 1
    with pytest.raises(CannotConnect):
        await cloud.set_property("1", HOST, 2, 4, 5)
    assert sum(1 for c in aioclient_mock.mock_calls if str(c[1]) == CMD_URL) == 2


async def test_rejected_write(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(TOKEN_URL, json=TOKEN)
    aioclient_mock.post(CMD_URL, json={"code": 0, "data": {"result": [{"siid": 2, "piid": 1, "code": -4002}]}})
    with pytest.raises(CommandFailed):
        await _cloud(hass).set_property("1", HOST, 2, 1, 1)


@pytest.mark.parametrize(
    ("path", "url"),
    [
        ("custom_components/dreame_air/api.py", "https://{self._region}.iot.dreame.tech:13267"),
        ("tools/probe.py", "https://{args.region}.iot.dreame.tech:13267"),
    ],
)
def test_only_dreame_cloud_hosts(path: str, url: str) -> None:
    # Credentials go to these URLs; any other host must be a deliberate, reviewed change.
    source = (Path(__file__).parent.parent / path).read_text(encoding="utf-8")
    assert re.findall(r"\w+://[^\s\"']+", source) == [url]
