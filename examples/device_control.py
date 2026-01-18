#!/usr/bin/env python3
"""Example showing device control via RPC commands."""

import asyncio
import os

from prana_api import PranaClient


async def main():
    """Demonstrate device control commands."""
    email = os.environ.get("PRANA_EMAIL")
    password = os.environ.get("PRANA_PASSWORD")

    if not email or not password:
        print("Please set PRANA_EMAIL and PRANA_PASSWORD environment variables")
        return

    async with PranaClient() as client:
        await client.login(email, password)
        print("Logged in!")

        devices = await client.get_user_devices()
        if not devices:
            print("No devices found")
            return

        device = devices[0]
        device_id = device.device_id
        print(f"\nUsing device: {device.name} ({device_id})")

        # Get current state
        state = await client.get_device_state(device_id)
        print(f"Current supply speed: {state.supply_speed}")
        print(f"Current extract speed: {state.extract_speed}")

        # Example: Simulate button clicks
        # Note: Button numbers correspond to physical buttons on the device
        # This is just an example - adjust based on your device's button mapping
        print("\n--- Button Control Examples ---")
        print("These are examples of how to send RPC commands.")
        print("Uncomment the code below to actually send commands.\n")

        # Uncomment to actually send commands:
        #
        # # Button 1 - typically power or mode toggle
        # print("Clicking button 1...")
        # await client.button_click(device_id, button_number=1)
        #
        # # Button 2 - typically speed up
        # print("Clicking button 2...")
        # await client.button_click(device_id, button_number=2)
        #
        # # Button 3 - typically speed down
        # print("Clicking button 3...")
        # await client.button_click(device_id, button_number=3)

        # Example: Set heater temperature
        # await client.set_auto_heater_temperature(device_id, temperature=20)

        # Example: Rename device
        # await client.rename_device(device_id, "My Prana Living Room")

        # Example: Send custom RPC command
        # You can send any RPC command supported by the device
        # result = await client.send_rpc_twoway(
        #     device_id,
        #     method="getConfiguration",
        #     params={},
        #     timeout=10000,
        # )
        # print(f"Configuration: {result}")

        print("Example complete!")
        await client.logout()


if __name__ == "__main__":
    asyncio.run(main())
