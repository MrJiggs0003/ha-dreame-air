#!/usr/bin/env python3
"""Read-only probe for mapping a Dreame purifier's properties.

It never writes. It reads one property at a time and asks before each read,
because reading the wrong property can crash some models (the TP20 reboots when
3/10 is read). Run it from a computer, not inside Home Assistant.

    python3 tools/probe.py --list
    python3 tools/probe.py --did 123456789 2/1 2/3 2/4 4/1

Standard library only. Your password is read with getpass and only its salted
hash is sent to Dreame, the same as the Dreamehome app.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import sys
import urllib.parse
import urllib.request

# Same protocol values as custom_components/dreame_air/api.py.
SALT = "RAylYC%fmSKp7%Tq"
USER_AGENT = "Dreame_Smarthome/2.1.9 (iPhone; iOS 18.4.1; Scale/3.00)"
CLIENT_AUTH = "Basic " + "ZHJlYW1lX2FwcHYx" + "OkFQXmR2QHpAU1FZVnhOODg="
RLC = "1c80b3787b2266776bcdc481f37d8fa42ba10a30af81a6df-1"


def post(url: str, headers: dict[str, str], body: bytes) -> dict:
    request = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT, **headers}, method="POST")  # noqa: S310
    with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310 - fixed https URL
        return json.loads(response.read())


def login(base: str, username: str, password: str) -> tuple[str, str]:
    form = urllib.parse.urlencode(
        {
            "platform": "IOS",
            "scope": "all",
            "grant_type": "password",
            "username": username,
            "password": hashlib.md5((password + SALT).encode()).hexdigest(),  # noqa: S324 - the app's scheme
            "type": "account",
        }
    ).encode()
    result = post(
        f"{base}/dreame-auth/oauth/token",
        {
            "Authorization": CLIENT_AUTH,
            "Tenant-Id": "000000",
            "Content-Type": "application/x-www-form-urlencoded",
            "Dreame-Rlc": RLC,
        },
        form,
    )
    if "access_token" not in result:
        sys.exit(f"Sign-in failed: {result.get('error_description') or result}")
    return result["access_token"], result.get("tenant_id", "000000")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--region", default="us", help="us, eu, sg, ru, kr or cn (default us)")
    parser.add_argument("--list", action="store_true", help="list purifiers on the account and exit")
    parser.add_argument("--did", help="device ID from --list")
    parser.add_argument("addresses", nargs="*", help="properties to read, as siid/piid, for example 2/1")
    args = parser.parse_args()

    base = f"https://{args.region}.iot.dreame.tech:13267"
    token, tenant = login(base, input("Dreamehome email: "), getpass.getpass("Password: "))
    headers = {
        "Authorization": CLIENT_AUTH,
        "Tenant-Id": tenant,
        "Dreame-Auth": token,
        "Content-Type": "application/json",
    }

    devices = post(f"{base}/dreame-user-iot/iotuserbind/device/listV2", headers, b"{}")["data"]["page"]["records"]
    if args.list or not args.did:
        for device in devices:
            print(f"{device.get('did')}  {device.get('model')}  {device.get('customName') or ''}")
        return

    device = next((d for d in devices if str(d.get("did")) == args.did), None)
    if device is None:
        sys.exit("No device with that ID on this account.")
    prefix = f"-{device['bindDomain'].split('.')[0]}" if device.get("bindDomain") else ""
    print(f"Probing {device.get('customName')} ({device.get('model')}). Reads only, one at a time.")
    print("If the purifier stops responding, stop and note the last address: it's unsafe on this model.\n")

    for address in args.addresses:
        siid, piid = (int(part) for part in address.split("/"))
        if input(f"Read {siid}/{piid}? [y/N] ").strip().lower() != "y":
            print("Stopped.")
            return
        params = [{"did": args.did, "siid": siid, "piid": piid}]
        payload = {
            "did": args.did,
            "id": 1,
            "data": {"did": args.did, "id": 1, "method": "get_properties", "params": params},
        }
        result = post(f"{base}/dreame-iot-com{prefix}/device/sendCommand", headers, json.dumps(payload).encode())
        print(f"  {siid}/{piid}: {json.dumps(result.get('data', {}).get('result', result))}")


if __name__ == "__main__":
    main()
