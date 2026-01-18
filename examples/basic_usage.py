#!/usr/bin/env python3
"""Basic usage example for the Prana API client."""

import asyncio
import os

from prana_api.client import PranaClient
from prana_api.models import PranaState


async def main():
    """Demonstrate basic Prana API usage."""
    # Get credentials from environment variables
    email = os.environ.get("PRANA_EMAIL") 
    password = os.environ.get("PRANA_PASSWORD")

    if not email or not password:
        print("Please set PRANA_EMAIL and PRANA_PASSWORD environment variables")
        print("Example:")
        print("  export PRANA_EMAIL='your@email.com'")
        print("  export PRANA_PASSWORD='yourpassword'")
        return

    async with PranaClient() as client:
        # Login
        print(f"Logging in as {email}...")
        await client.login(email, password)
        print("Login successful!")

        # Get user info
        user = await client.get_user()
        print(f"\nWelcome, {user.first_name} {user.last_name}!")

        # Get all devices
        print("\nFetching devices...")
        devices = await client.get_user_devices()
        print(f"Found {len(devices)} device(s)\n")

        for device in devices:
            print(f"{'=' * 50}")
            print(f"Device: {device.display_name}")
            print(f"ID: {device.device_id}")
            if device.prana_type:
                print(f"Model: {device.prana_type}")

            # Get device state
            try:
                state = await client.get_device_state(device.device_id)
                print_device_state(state)
            except Exception as e:
                print(f"Could not get state: {e}")

            print()

        # Example: Get raw telemetry for first device
        if devices:
            first_device = devices[0]
            print(f"\nRaw telemetry for {first_device.display_name}:")
            telemetry = await client.get_device_telemetry(
                first_device.device_id,
                keys=["motorsSup", "motorsExt", "co2", "voc", "temperature_2", "humidity"],
                limit=5,
            )
            for key, values in telemetry.items():
                print(f"  {key}: {values}")

        # Logout
        await client.logout()
        print("\nLogged out successfully!")


def print_device_state(state: PranaState):
    """Pretty print device state."""
    print("\nCurrent State:")
    print(f"  Online: {'✓' if state.is_online else '✗'}")
    print(f"  Power: {'ON' if state.is_power_on else 'OFF'}")

    # Speed (0-5 scale)
    if state.supply_speed is not None or state.extract_speed is not None:
        print(f"  Supply Speed (incoming): {state.supply_speed or 0}/5")
        print(f"  Extract Speed (outgoing): {state.extract_speed or 0}/5")

    # Modes
    modes = []
    if state.is_auto_mode:
        modes.append("Auto")
    if state.is_bounded_mode:
        modes.append("Bounded")
    if state.is_night_mode:
        modes.append("Night")
    if state.is_heater_on:
        modes.append("Heater")
    if state.is_defrosting:
        modes.append("Defrosting")
    if modes:
        print(f"  Active Modes: {', '.join(modes)}")

    # Timer
    if state.is_sleep_timer and state.sleep_seconds > 0:
        minutes = state.sleep_seconds // 60
        print(f"  Sleep Timer: {minutes} minutes remaining")

    # Sensors
    if state.temperature is not None:
        print(f"  Temperature: {state.temperature}°C")
    if state.humidity is not None and state.humidity > 0:
        print(f"  Humidity: {state.humidity}%")
    if state.co2 is not None and state.co2 > 0:
        print(f"  CO2: {state.co2} ppm")
    if state.voc is not None and state.voc > 0:
        print(f"  VOC: {state.voc}")

    # Status
    if state.wifi_rssi is not None:
        print(f"  WiFi Signal: {state.wifi_rssi} dBm")
    if state.firmware_version is not None:
        print(f"  Firmware: v{state.firmware_version}")
    if state.last_activity_time:
        print(f"  Last Activity: {state.last_activity_time}")


if __name__ == "__main__":
    asyncio.run(main())
