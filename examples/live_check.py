"""Exercise the miot client against a real vacuum.

Reads XIAOMI_VACUUM_HOST and XIAOMI_VACUUM_TOKEN from the environment (or a
local .env), performs the miIO.info handshake and reads one property by
address (defaults to the X20 Max map-object property, siid 10 / piid 1).
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from xiaomi_vacuum_sdk import MiotClient, PropertyAddress


async def main() -> None:
    load_dotenv()
    host = os.environ["XIAOMI_VACUUM_HOST"]
    token = os.environ["XIAOMI_VACUUM_TOKEN"]
    siid = int(os.environ.get("XIAOMI_VACUUM_SIID", "10"))
    piid = int(os.environ.get("XIAOMI_VACUUM_PIID", "1"))

    client = MiotClient(host, token)
    try:
        info = await client.info()
        print(f"model={info.model} firmware={info.firmware_version} mac={info.mac_address}")
        values = await client.get_properties({"probe": PropertyAddress(siid=siid, piid=piid)})
        print(f"property {siid}/{piid} = {values['probe']!r}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
