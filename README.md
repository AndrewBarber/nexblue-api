# NexBlue API

`nexblue-api` is the official asynchronous Python client for the NexBlue OpenAPI.
It is maintained by NexBlue and currently provides the communication layer used by
the NexBlue Home Assistant integration.

The package handles authentication, access-token refresh, charger discovery,
charger telemetry, and start/stop charging commands. It is deliberately independent
of Home Assistant so it can be reused by other Python applications.

## Requirements

- Python 3.13 or later
- A NexBlue account with access to the NexBlue OpenAPI

Installing this library does not create, grant, or expand access to a NexBlue
account or service.

## Installation

```bash
pip install nexblue-api
```

## Basic usage

Keep credentials outside source code. The example uses environment variables and a
placeholder API base URL supplied by NexBlue.

```python
import asyncio
import os

import aiohttp

from nexblue_api import NexBlueClient


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = NexBlueClient(
            session,
            os.environ["NEXBLUE_API_BASE_URL"],
        )

        await client.async_login(
            os.environ["NEXBLUE_USERNAME"],
            os.environ["NEXBLUE_PASSWORD"],
        )

        for charger in await client.async_list_chargers():
            status = await client.async_get_charger_status(charger.serial_number)
            print(charger.serial_number, status.charging_state, status.power_kw)


asyncio.run(main())
```

## Supported operations

- End-user login and refresh-token based access-token renewal
- Charger discovery
- Charger status and telemetry retrieval
- Start charging and stop charging commands
- Aggregated energy consumption (owner and installer accounts)
- Typed charger, status, and token models
- Safe exceptions for authentication, connection, rate-limit, offline-device, and
  rejected-command errors

Status values are normalized to the API's documented units: kW, kWh, A, and V.
Charging commands can still be rejected by the API or charger, for example when the
charger is offline or another user is controlling it.

## Credential handling

Do not commit, log, or share usernames, passwords, access tokens, refresh tokens,
or OAuth client credentials.

The client retains tokens only for its active lifetime. Applications that need to
restore a session should persist only the refresh token using their platform's
protected credential storage, then call `async_refresh_access_token`. Do not persist
an end-user password merely to perform automatic logins.

Successful login and refresh calls return a `TokenBundle`. Its `account_id` field is
the stable account subject provided by the access token when available. Applications
may use this value as a local, non-secret account identifier; they should not derive
identity from a username or log the access token itself.

This library does not embed NexBlue OAuth client credentials. Applications using an
external OAuth flow may provide an externally managed access token with
`set_access_token`.

## Development

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
```

Please report bugs through the repository issue tracker. Do not include credentials,
tokens, full API responses, or personally identifiable charger information in issues.

## License

Copyright 2026 NexBlue.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
