#!/usr/bin/env python3
"""Example showing synchronous API usage."""

import os

from prana_api import PranaClientSync


def main():
    """Demonstrate synchronous Prana API usage."""
    email = os.environ.get("PRANA_EMAIL")
    password = os.environ.get("PRANA_PASSWORD")

    if not email or not password:
        print("Please set PRANA_EMAIL and PRANA_PASSWORD environment variables")
        return

    # Create sync client
    client = PranaClientSync()

    try:
        # Login
        print(f"Logging in as {email}...")
        client.login(email, password)
        print("Login successful!")

        # Get user
        user = client.get_user()
        print(f"Welcome, {user.first_name}!")

        # Get devices
        devices = client.get_user_devices()
        print(f"\nFound {len(devices)} device(s):")

        for device in devices:
            print(f"\n  - {device.name} ({device.device_id})")

            # Get state
            state = client.get_device_state(device.device_id)
            print(f"    Supply: {state.supply_speed}, Extract: {state.extract_speed}")
            if state.temperature:
                print(f"    Temperature: {state.temperature}°C")

        # Logout
        client.logout()
        print("\nLogged out!")

    finally:
        # Always close the client
        client.close()


if __name__ == "__main__":
    main()
