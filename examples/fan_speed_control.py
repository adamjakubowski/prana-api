#!/usr/bin/env python3
"""Example demonstrating independent fan speed control for Prana ventilation devices.

This example shows how to control the incoming (supply) and outgoing (extract)
air fan speeds independently using the Prana API.

The Prana device has two fans:
- Supply fan: Controls incoming (fresh) air from outside
- Extract fan: Controls outgoing (exhaust) air to outside

Speed values range from 0 (off) to 5 (maximum).

Bounded Mode:
When bounded mode is enabled, both fans are linked and speed changes affect
both fans simultaneously using buttons 2/3. When disabled, you can control
each fan independently using the dedicated methods (set_supply_speed,
set_extract_speed) or buttons 8-11.
"""

import asyncio
import os

from prana_api import PranaClient, ButtonNumber


async def display_current_state(client: PranaClient, device_id: str) -> None:
    """Display current fan speeds and mode information."""
    state = await client.get_device_state(device_id)

    print("\n--- Current Device State ---")
    print(f"  Supply speed (incoming):  {state.supply_speed or 0}/5")
    print(f"  Extract speed (outgoing): {state.extract_speed or 0}/5")
    print(f"  Bounded mode (linked):    {'Yes' if state.is_bounded_mode else 'No'}")
    print(f"  Power:                    {'ON' if state.is_power_on else 'OFF'}")
    print(f"  Auto mode:                {'Yes' if state.is_auto_mode else 'No'}")
    print(f"  Night mode:               {'Yes' if state.is_night_mode else 'No'}")

    return state


async def example_independent_fan_control(client: PranaClient, device_id: str) -> None:
    """Example: Control supply and extract fans independently."""
    print("\n=== Independent Fan Control ===")
    print("This example shows how to set different speeds for supply and extract fans.")

    # Show current state
    await display_current_state(client, device_id)

    # Set supply fan to speed 3
    print("\nSetting supply fan to speed 3...")
    await client.set_supply_speed(device_id, target_speed=3)
    await asyncio.sleep(1)

    await display_current_state(client, device_id)

    # Set extract fan to speed 2
    print("\nSetting extract fan to speed 2...")
    await client.set_extract_speed(device_id, target_speed=2)
    await asyncio.sleep(1)

    await display_current_state(client, device_id)


async def example_step_control(client: PranaClient, device_id: str) -> None:
    """Example: Step-by-step control of individual fans."""
    print("\n=== Step Control ===")
    print("This example shows how to increase/decrease individual fan speeds by one step.")

    await display_current_state(client, device_id)

    # Increase supply speed by one step
    print("\nIncreasing supply fan speed by one step...")
    await client.supply_speed_up(device_id)
    await asyncio.sleep(1)
    await display_current_state(client, device_id)

    # Increase extract speed by one step
    print("\nIncreasing extract fan speed by one step...")
    await client.extract_speed_up(device_id)
    await asyncio.sleep(1)
    await display_current_state(client, device_id)

    # Decrease supply speed by one step
    print("\nDecreasing supply fan speed by one step...")
    await client.supply_speed_down(device_id)
    await asyncio.sleep(1)
    await display_current_state(client, device_id)


async def example_bounded_mode(client: PranaClient, device_id: str) -> None:
    """Example: Toggle bounded mode."""
    print("\n=== Bounded Mode Control ===")
    print("Bounded mode links the two fans - they operate at the same speed.")
    print("When off, fans can be controlled independently.")

    state = await display_current_state(client, device_id)
    current_bounded = state.is_bounded_mode

    # Toggle bounded mode
    print(f"\nToggling bounded mode (currently {'ON' if current_bounded else 'OFF'})...")
    await client.toggle_bounded_mode(device_id)
    await asyncio.sleep(1)

    state = await display_current_state(client, device_id)
    print(f"Bounded mode is now {'ON' if state.is_bounded_mode else 'OFF'}")

    # Restore original state
    if state.is_bounded_mode != current_bounded:
        print("\nRestoring original bounded mode state...")
        await client.toggle_bounded_mode(device_id)
        await asyncio.sleep(1)
        await display_current_state(client, device_id)


async def example_button_numbers(client: PranaClient, device_id: str) -> None:
    """Example: Show available button numbers for direct control."""
    print("\n=== Button Number Reference ===")
    print("These button numbers can be used with client.button_click():")
    print("")
    print(f"  Power:              {ButtonNumber.POWER}")
    print(f"  Speed Up (both):    {ButtonNumber.SPEED_UP}")
    print(f"  Speed Down (both):  {ButtonNumber.SPEED_DOWN}")
    print(f"  Night Mode:         {ButtonNumber.NIGHT_MODE}")
    print(f"  Auto Mode:          {ButtonNumber.AUTO_MODE}")
    print(f"  Heater:             {ButtonNumber.HEATER}")
    print(f"  Bounded Mode:       {ButtonNumber.BOUNDED_MODE}")
    print(f"  Supply Speed Up:    {ButtonNumber.SUPPLY_SPEED_UP}")
    print(f"  Supply Speed Down:  {ButtonNumber.SUPPLY_SPEED_DOWN}")
    print(f"  Extract Speed Up:   {ButtonNumber.EXTRACT_SPEED_UP}")
    print(f"  Extract Speed Down: {ButtonNumber.EXTRACT_SPEED_DOWN}")
    print(f"  Sleep Timer:        {ButtonNumber.SLEEP_TIMER}")
    print(f"  Brightness:         {ButtonNumber.BRIGHTNESS}")
    print("")
    print("Example usage:")
    print("  await client.button_click(device_id, ButtonNumber.SUPPLY_SPEED_UP)")


async def example_set_different_speeds(client: PranaClient, device_id: str) -> None:
    """Example: Set supply and extract to specific different speeds."""
    print("\n=== Set Different Speeds ===")
    print("Setting supply=4, extract=2 for asymmetric ventilation...")

    await display_current_state(client, device_id)

    # Store original speeds
    state = await client.get_device_state(device_id)
    original_supply = state.supply_speed or 0
    original_extract = state.extract_speed or 0

    # Set supply to 4
    print("\nSetting supply fan to speed 4...")
    await client.set_supply_speed(device_id, target_speed=4)
    await asyncio.sleep(1)

    # Set extract to 2
    print("Setting extract fan to speed 2...")
    await client.set_extract_speed(device_id, target_speed=2)
    await asyncio.sleep(1)

    await display_current_state(client, device_id)

    # Restore original speeds
    print(f"\nRestoring original speeds (supply={original_supply}, extract={original_extract})...")
    await client.set_supply_speed(device_id, target_speed=original_supply)
    await client.set_extract_speed(device_id, target_speed=original_extract)
    await asyncio.sleep(1)

    await display_current_state(client, device_id)


async def main():
    """Main example demonstrating independent fan speed control."""
    email = os.environ.get("PRANA_EMAIL")
    password = os.environ.get("PRANA_PASSWORD")

    if not email or not password:
        print("Please set PRANA_EMAIL and PRANA_PASSWORD environment variables")
        print("")
        print("Example:")
        print('  export PRANA_EMAIL="your@email.com"')
        print('  export PRANA_PASSWORD="yourpassword"')
        return

    async with PranaClient() as client:
        await client.login(email, password)
        print("Logged in successfully!")

        # Get devices
        devices = await client.get_user_devices()
        if not devices:
            print("No devices found")
            return

        # Use first device (or modify to select specific device)
        device = devices[0]
        device_id = device.device_id
        print(f"\nUsing device: {device.name} ({device_id})")

        # Show current state
        await display_current_state(client, device_id)

        # Show button number reference
        await example_button_numbers(client, device_id)

        # Run examples (uncomment to execute):

        # Example 1: Set different speeds for supply and extract
        # await example_set_different_speeds(client, device_id)

        # Example 2: Step-by-step control
        # await example_step_control(client, device_id)

        # Example 3: Toggle bounded mode
        # await example_bounded_mode(client, device_id)

        # Example 4: Full independent control
        # await example_independent_fan_control(client, device_id)

        print("\nExample complete!")
        await client.logout()


if __name__ == "__main__":
    asyncio.run(main())
