"""Prana API Client Library.

A Python library for interacting with the Prana ventilation system API.
The API is built on ThingsBoard PE (Professional Edition) IoT platform.

Example usage:
    ```python
    from prana_api import PranaClient

    async def main():
        async with PranaClient() as client:
            await client.login("email@example.com", "password")

            # Get all devices
            devices = await client.get_user_devices()

            for device in devices:
                # Get current state
                state = await client.get_device_state(device.device_id)
                print(f"{device.name}: Supply={state.supply_speed}, Extract={state.extract_speed}")

                # Control device via button click
                await client.button_click(device.device_id, button_number=1)

    import asyncio
    asyncio.run(main())
    ```

For synchronous usage:
    ```python
    from prana_api import PranaClientSync

    client = PranaClientSync()
    client.login("email@example.com", "password")
    devices = client.get_user_devices()
    client.close()
    ```
"""

__version__ = "0.1.0"
__author__ = "Prana API Contributors"

from .client import PranaClient, PranaClientSync
from .constants import (
    BASE_URL,
    AttributeScope,
    DeviceStateKey,
    Endpoints,
    EntityType,
    RPCMethod,
    SLEEP_TIMER_OPTIONS,
)
from .exceptions import (
    AuthenticationError,
    DeviceNotFoundError,
    InvalidCredentialsError,
    NetworkError,
    PranaAPIError,
    RateLimitError,
    RPCError,
    TokenExpiredError,
    UserNotActiveError,
)
from .models import (
    Device,
    EntityGroup,
    EntityId,
    PageData,
    PranaState,
    Scenario,
    TokenPair,
    User,
)

__all__ = [
    # Client
    "PranaClient",
    "PranaClientSync",
    # Constants
    "BASE_URL",
    "AttributeScope",
    "DeviceStateKey",
    "Endpoints",
    "EntityType",
    "RPCMethod",
    "SLEEP_TIMER_OPTIONS",
    # Exceptions
    "AuthenticationError",
    "DeviceNotFoundError",
    "InvalidCredentialsError",
    "NetworkError",
    "PranaAPIError",
    "RateLimitError",
    "RPCError",
    "TokenExpiredError",
    "UserNotActiveError",
    # Models
    "Device",
    "EntityGroup",
    "EntityId",
    "PageData",
    "PranaState",
    "Scenario",
    "TokenPair",
    "User",
]
