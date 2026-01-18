# Prana API

> **⚠️ Work in Progress**: This library is under active development. I cannot guarantee that it's working correctly. Use at your own risk.

A Python library for interacting with the Prana ventilation system API.

The Prana API is built on [ThingsBoard PE](https://thingsboard.io/) (Professional Edition) IoT platform, hosted at `https://iot.sensesaytech.com`.

## Installation

```bash
pip install prana-api
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

### Async Usage (Recommended)

```python
import asyncio
from prana_api import PranaClient

async def main():
    async with PranaClient() as client:
        # Login
        await client.login("your@email.com", "password")

        # Get all devices
        devices = await client.get_user_devices()

        for device in devices:
            print(f"Device: {device.name}")

            # Get current state
            state = await client.get_device_state(device.device_id)
            print(f"  Supply Speed: {state.supply_speed}")
            print(f"  Extract Speed: {state.extract_speed}")
            print(f"  Temperature: {state.temperature}°C")

        # Logout
        await client.logout()

asyncio.run(main())
```

### Synchronous Usage

```python
from prana_api import PranaClientSync

client = PranaClientSync()

client.login("your@email.com", "password")

devices = client.get_user_devices()
for device in devices:
    state = client.get_device_state(device.device_id)
    print(f"{device.name}: {state.supply_speed}/{state.extract_speed}")

client.logout()
client.close()
```

## Features

- **Authentication**: Login, logout, token refresh, password change/reset
- **Device Management**: List devices, get device info
- **Telemetry**: Read device sensor data (temperature, humidity, CO2, VOC)
- **Device Control**: Send RPC commands to control devices
- **Entity Groups**: Manage device groups

## API Reference

### PranaClient

The main async client class.

```python
async with PranaClient(
    base_url="https://iot.sensesaytech.com",  # API base URL
    timeout=30.0,                              # Request timeout in seconds
    auto_refresh=True,                         # Auto-refresh expired tokens
) as client:
    ...
```

#### Authentication

```python
# Login
await client.login(username, password)

# Logout
await client.logout()

# Refresh token (usually automatic)
await client.refresh_token()

# Change password
await client.change_password(current_password, new_password)
```

#### Devices

```python
# Get all user devices
devices = await client.get_user_devices()

# Get specific device
device = await client.get_device(device_id)

# Get device state (parsed telemetry)
state = await client.get_device_state(device_id)
```

#### Telemetry & Attributes

```python
# Get raw telemetry data
telemetry = await client.get_device_telemetry(
    device_id,
    keys=["temperature", "humidity", "co2"],
    limit=100,
)

# Get device attributes
attributes = await client.get_device_attributes(
    device_id,
    scope="SHARED_SCOPE",  # or SERVER_SCOPE, CLIENT_SCOPE
)
```

#### Device Control (RPC)

```python
# Send one-way command (no response)
await client.send_rpc_oneway(device_id, "methodName", {"param": "value"})

# Send two-way command (with response)
result = await client.send_rpc_twoway(device_id, "methodName", {"param": "value"})

# Convenience methods
await client.button_click(device_id, button_number=1)
await client.rename_device(device_id, "New Name")
await client.set_auto_heater_temperature(device_id, temperature=20)
```

### Models

#### PranaState

Represents the current state of a Prana device:

```python
@dataclass
class PranaState:
    # Speed (0-10)
    supply_speed: int | None
    extract_speed: int | None

    # Modes
    is_auto: bool
    is_auto_plus: bool
    is_boost_mode: bool
    is_night_mode: bool
    is_winter: bool
    is_heater: bool

    # Timer
    is_sleep_timer: bool
    seconds_sleep_timer: int

    # Settings
    brightness: int | None
    heater_temperature: int | None

    # Sensors
    co2: int | None
    voc: int | None
    humidity: float | None
    temperature: float | None

    # Status
    is_online: bool
    is_defrosting: bool
```

### Exceptions

```python
from prana_api import (
    PranaAPIError,           # Base exception
    AuthenticationError,     # Auth failed
    InvalidCredentialsError, # Wrong username/password
    UserNotActiveError,      # Account not activated
    TokenExpiredError,       # Token expired
    DeviceNotFoundError,     # Device not found
    RPCError,                # RPC command failed
    RateLimitError,          # Rate limit exceeded
    NetworkError,            # Network error
)
```

## Known RPC Methods

Based on reverse engineering, these RPC methods are available:

| Method | Parameters | Description |
|--------|------------|-------------|
| `buttonClicked` | `{"buttonNumber": int}` | Simulate button press |
| `renameDeviceV2` | `{"deviceName": str}` | Rename device |
| `setAutoHeaterTemperature` | `{"autoHeaterTemperature": int}` | Set heater temp |
| `setScenariosV2` | `{"scenarios": [...]}` | Set schedules |
| `setFw` | `{"fw": str}` | Update firmware |

## Environment Variables

For the examples, set these environment variables:

```bash
export PRANA_EMAIL="your@email.com"
export PRANA_PASSWORD="yourpassword"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy prana_api

# Lint
ruff check prana_api
```

## License

MIT License

## Disclaimer

This is an unofficial API client created through reverse engineering. It is not affiliated with or endorsed by Prana. Use at your own risk.
