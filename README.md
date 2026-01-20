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

### Independent Fan Control

```python
import asyncio
from prana_api import PranaClient

async def main():
    async with PranaClient() as client:
        await client.login("your@email.com", "password")

        devices = await client.get_user_devices()
        device_id = devices[0].device_id

        # Set different speeds for incoming and outgoing air
        await client.set_supply_speed(device_id, target_speed=4)   # Incoming air
        await client.set_extract_speed(device_id, target_speed=2)  # Outgoing air

        # Check result
        state = await client.get_device_state(device_id)
        print(f"Supply: {state.supply_speed}, Extract: {state.extract_speed}")
        print(f"Bounded mode: {state.is_bounded_mode}")

asyncio.run(main())
```

## Features

- **Authentication**: Login, logout, token refresh, password change/reset
- **Device Management**: List devices, get device info
- **Telemetry**: Read device sensor data (temperature, humidity, CO2, VOC, pressure)
- **Fan Speed Control**: Independent control of supply (incoming) and extract (outgoing) fans
- **Mode Control**: Toggle bounded mode, night mode, auto mode, heater
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

#### Fan Speed Control

The Prana device has two fans that can be controlled independently:
- **Supply fan**: Controls incoming (fresh) air from outside
- **Extract fan**: Controls outgoing (exhaust) air to outside

Speed values range from 0 (off) to 5 (maximum).

```python
# Control both fans together (bounded mode)
await client.speed_up(device_id)      # Increase both fans
await client.speed_down(device_id)    # Decrease both fans
await client.set_fan_speed(device_id, target_speed=3)

# Control fans independently
await client.set_supply_speed(device_id, target_speed=4)   # Set incoming air
await client.set_extract_speed(device_id, target_speed=2)  # Set outgoing air

# Step control for individual fans
await client.supply_speed_up(device_id)
await client.supply_speed_down(device_id)
await client.extract_speed_up(device_id)
await client.extract_speed_down(device_id)

# Toggle bounded mode (link/unlink fans)
await client.toggle_bounded_mode(device_id)
```

**Bounded Mode**: When enabled, both fans operate at the same speed. When disabled, fans can be controlled independently using the methods above.

### Models

#### PranaState

Represents the current state of a Prana device:

```python
@dataclass
class PranaState:
    # Speed (0-5)
    supply_speed: int | None   # Incoming air fan speed
    extract_speed: int | None  # Outgoing air fan speed

    # Modes
    is_power_on: bool
    is_auto_mode: bool
    is_bounded_mode: bool  # True = fans linked, False = independent control
    is_night_mode: bool
    is_heater_on: bool

    # Timer
    is_sleep_timer: bool
    sleep_seconds: int

    # Settings
    brightness: int | None

    # Sensors
    co2: int | None
    voc: int | None
    humidity: float | None
    temperature: float | None
    pressure: int | None

    # Status
    is_online: bool
    is_defrosting: bool
    wifi_rssi: int | None
    firmware_version: int | None
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

## Button Numbers

The device is controlled by sending `buttonClicked` RPC commands with a button number.
These are available as constants in the `ButtonNumber` class:

```python
from prana_api import ButtonNumber

await client.button_click(device_id, ButtonNumber.SUPPLY_SPEED_UP)
```

| Button | Number | Description |
|--------|--------|-------------|
| `POWER` | 1 | Toggle power on/off |
| `SPEED_UP` | 2 | Increase fan speed (both fans in bounded mode) |
| `SPEED_DOWN` | 3 | Decrease fan speed (both fans in bounded mode) |
| `NIGHT_MODE` | 4 | Toggle night mode |
| `AUTO_MODE` | 5 | Toggle auto mode |
| `HEATER` | 6 | Toggle heater (winter mode) |
| `BOUNDED_MODE` | 7 | Toggle bounded mode (link/unlink fans) |
| `SUPPLY_SPEED_UP` | 8 | Increase supply (incoming) fan speed |
| `SUPPLY_SPEED_DOWN` | 9 | Decrease supply (incoming) fan speed |
| `EXTRACT_SPEED_UP` | 10 | Increase extract (outgoing) fan speed |
| `EXTRACT_SPEED_DOWN` | 11 | Decrease extract (outgoing) fan speed |
| `SLEEP_TIMER` | 12 | Toggle or cycle sleep timer |
| `BRIGHTNESS` | 13 | Cycle display brightness |

> **Note**: Button mappings may vary by device model or firmware version. Test carefully with your specific device.

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
