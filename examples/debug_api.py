#!/usr/bin/env python3
"""Debug script to inspect raw API responses."""

import asyncio
import json
import os

import httpx


async def main():
    email = os.environ.get("PRANA_EMAIL") 
    password = os.environ.get("PRANA_PASSWORD") 

    base_url = "https://iot.sensesaytech.com"

    async with httpx.AsyncClient() as client:
        # Login
        print("Logging in...")
        resp = await client.post(
            f"{base_url}/api/auth/login",
            json={"username": email, "password": password},
        )
        tokens = resp.json()
        access_token = tokens.get("token")
        print(f"Got token: {access_token[:50]}...")

        headers = {"Authorization": f"Bearer {access_token}"}

        # Get user
        print("\n=== USER INFO ===")
        resp = await client.get(f"{base_url}/api/auth/user", headers=headers)
        user = resp.json()
        print(json.dumps(user, indent=2))

        customer_id = user.get("customerId", {}).get("id")
        print(f"\nCustomer ID: {customer_id}")

        # Get devices
        print("\n=== DEVICES (raw) ===")
        resp = await client.get(
            f"{base_url}/api/customer/{customer_id}/devices",
            params={"page": 0, "pageSize": 10},
            headers=headers,
        )
        devices_data = resp.json()
        print(json.dumps(devices_data, indent=2))

        # Get first device telemetry
        if devices_data.get("data"):
            first_device = devices_data["data"][0]
            device_id = first_device.get("id", {}).get("id")
            print(f"\n=== TELEMETRY for device {device_id} ===")
            resp = await client.get(
                f"{base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
                params={"limit": 5},
                headers=headers,
            )
            telemetry = resp.json()
            print(json.dumps(telemetry, indent=2))

            print(f"\n=== ATTRIBUTES for device {device_id} ===")
            resp = await client.get(
                f"{base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes",
                headers=headers,
            )
            attributes = resp.json()
            print(json.dumps(attributes, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
