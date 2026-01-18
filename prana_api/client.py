"""Main Prana API client."""

import asyncio
from typing import Any

import httpx

from .auth import TokenManager
from .constants import (
    BASE_URL,
    DEFAULT_RPC_TIMEOUT,
    DEFAULT_TIMEOUT,
    AttributeScope,
    EntityType,
    Endpoints,
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
    TokenPair,
    User,
)


class PranaClient:
    """Async client for the Prana IoT API.

    This client provides access to the Prana ventilation system API,
    which is built on ThingsBoard PE platform.

    Example:
        ```python
        async with PranaClient() as client:
            await client.login("email@example.com", "password")
            devices = await client.get_user_devices()
            for device in devices:
                state = await client.get_device_state(device.device_id)
                print(f"{device.name}: Speed {state.supply_speed}")
        ```
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        auto_refresh: bool = True,
    ):
        """Initialize the Prana API client.

        Args:
            base_url: Base URL for the API (default: https://iot.sensesaytech.com)
            timeout: Default timeout for requests in seconds
            auto_refresh: Automatically refresh token when expired
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auto_refresh = auto_refresh
        self._token_manager = TokenManager()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PranaClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._token_manager.is_authenticated

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _get_headers(self, include_auth: bool = True) -> dict[str, str]:
        """Get request headers.

        Args:
            include_auth: Include Authorization header if authenticated

        Returns:
            Headers dict
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if include_auth:
            headers.update(self._token_manager.get_authorization_header())
        return headers

    async def _check_and_refresh_token(self) -> None:
        """Check if token needs refresh and refresh it."""
        if (
            self.auto_refresh
            and self._token_manager.is_authenticated
            and self._token_manager.is_access_token_expired
            and not self._token_manager.is_refresh_token_expired
        ):
            await self.refresh_token()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        include_auth: bool = True,
    ) -> Any:
        """Make an API request.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            include_auth: Include Authorization header

        Returns:
            Response JSON data

        Raises:
            PranaAPIError: On API errors
            NetworkError: On network errors
        """
        if include_auth:
            await self._check_and_refresh_token()

        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)
        client = self._get_client()

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}") from e

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response.

        Args:
            response: HTTP response

        Returns:
            Response data

        Raises:
            Various exceptions based on status code
        """
        if response.status_code == 200:
            if response.content:
                try:
                    return response.json()
                except Exception:
                    return response.text
            return None

        if response.status_code == 401:
            try:
                error_data = response.json()
                message = error_data.get("message", "Authentication failed")
            except Exception:
                message = "Authentication failed"

            if "Invalid username or password" in message:
                raise InvalidCredentialsError(message, 401, response)
            elif "not active" in message:
                raise UserNotActiveError(message, 401, response)
            elif "expired" in message.lower():
                raise TokenExpiredError(message, 401, response)
            raise AuthenticationError(message, 401, response)

        if response.status_code == 404:
            raise DeviceNotFoundError("Resource not found", 404, response)

        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded", 429, response)

        # Generic error handling
        try:
            error_data = response.json()
            message = error_data.get("message", f"API error: {response.status_code}")
        except Exception:
            message = f"API error: {response.status_code}"

        raise PranaAPIError(message, response.status_code, response)

    # ==================== Authentication ====================

    async def login(self, username: str, password: str) -> TokenPair:
        """Login with username (email) and password.

        Args:
            username: User email
            password: User password

        Returns:
            TokenPair with access and refresh tokens

        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserNotActiveError: If user account is not active
        """
        data = await self._request(
            "POST",
            Endpoints.AUTH_LOGIN,
            json_data={"username": username, "password": password},
            include_auth=False,
        )

        token_pair = TokenPair.from_response(data)
        self._token_manager.set_tokens(token_pair)
        return token_pair

    async def refresh_token(self) -> TokenPair:
        """Refresh the access token using refresh token.

        Returns:
            New TokenPair

        Raises:
            TokenExpiredError: If refresh token is expired
        """
        if not self._token_manager.refresh_token:
            raise TokenExpiredError("No refresh token available")

        data = await self._request(
            "POST",
            Endpoints.AUTH_TOKEN,
            json_data={"refreshToken": self._token_manager.refresh_token},
            include_auth=False,
        )

        token_pair = TokenPair.from_response(data)
        self._token_manager.set_tokens(token_pair)
        return token_pair

    async def logout(self) -> None:
        """Logout and invalidate tokens."""
        try:
            await self._request("POST", Endpoints.AUTH_LOGOUT)
        finally:
            self._token_manager.clear_tokens()

    async def change_password(
        self, current_password: str, new_password: str
    ) -> None:
        """Change user password.

        Args:
            current_password: Current password
            new_password: New password
        """
        await self._request(
            "POST",
            Endpoints.AUTH_CHANGE_PASSWORD,
            json_data={
                "currentPassword": current_password,
                "newPassword": new_password,
            },
        )

    # ==================== Registration (No Auth) ====================

    async def signup(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        recaptcha_response: str | None = None,
    ) -> dict[str, Any]:
        """Register a new user account.

        Args:
            email: User email
            password: Password
            first_name: First name
            last_name: Last name
            recaptcha_response: reCAPTCHA response token

        Returns:
            Registration response
        """
        data = {
            "email": email,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
        }
        if recaptcha_response:
            data["recaptchaResponse"] = recaptcha_response

        return await self._request(
            "POST",
            Endpoints.NOAUTH_SIGNUP,
            json_data=data,
            include_auth=False,
        )

    async def activate_by_email_code(self, email_code: str) -> dict[str, Any]:
        """Activate user account by email code.

        Args:
            email_code: Activation code from email

        Returns:
            Activation response
        """
        return await self._request(
            "POST",
            Endpoints.NOAUTH_ACTIVATE,
            json_data={"emailCode": email_code},
            include_auth=False,
        )

    async def request_password_reset(self, email: str) -> None:
        """Request password reset email.

        Args:
            email: User email
        """
        await self._request(
            "POST",
            Endpoints.NOAUTH_RESET_PASSWORD_REQUEST,
            json_data={"email": email},
            include_auth=False,
        )

    async def reset_password(self, reset_token: str, password: str) -> None:
        """Reset password using reset token.

        Args:
            reset_token: Token from password reset email
            password: New password
        """
        await self._request(
            "POST",
            Endpoints.NOAUTH_RESET_PASSWORD,
            json_data={"resetToken": reset_token, "password": password},
            include_auth=False,
        )

    # ==================== User ====================

    async def get_user(self) -> User:
        """Get current user info.

        Returns:
            Current user
        """
        data = await self._request("GET", Endpoints.AUTH_USER)
        return User.from_dict(data)

    # ==================== Devices ====================

    async def get_user_devices(
        self,
        page: int = 0,
        page_size: int = 100,
        text_search: str | None = None,
    ) -> list[Device]:
        """Get all devices belonging to the current user.

        Args:
            page: Page number (0-indexed)
            page_size: Number of items per page
            text_search: Optional text search filter

        Returns:
            List of devices
        """
        # Get customer ID from token
        customer_id = self._token_manager.get_customer_id()
        if not customer_id:
            # Try to get from user info
            user = await self.get_user()
            if user.customer_id:
                customer_id = user.customer_id.id

        if not customer_id:
            raise PranaAPIError("Could not determine customer ID")

        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }
        if text_search:
            params["textSearch"] = text_search

        endpoint = f"{Endpoints.CUSTOMER}/{customer_id}/devices"
        data = await self._request("GET", endpoint, params=params)
        page_data = PageData.from_dict(data, Device.from_dict)
        return page_data.data

    async def get_device(self, device_id: str) -> Device:
        """Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device

        Raises:
            DeviceNotFoundError: If device not found
        """
        data = await self._request("GET", f"{Endpoints.DEVICE}/{device_id}")
        return Device.from_dict(data)

    # ==================== Telemetry ====================

    async def get_device_telemetry(
        self,
        device_id: str,
        keys: list[str] | None = None,
        start_ts: int | None = None,
        end_ts: int | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get device telemetry data.

        Args:
            device_id: Device ID
            keys: Specific telemetry keys to fetch (None for all)
            start_ts: Start timestamp in milliseconds
            end_ts: End timestamp in milliseconds
            limit: Maximum number of values per key

        Returns:
            Telemetry data as dict
        """
        endpoint = f"{Endpoints.TELEMETRY}/{EntityType.DEVICE}/{device_id}/values/timeseries"
        params: dict[str, Any] = {"limit": limit}
        if keys:
            params["keys"] = ",".join(keys)
        if start_ts:
            params["startTs"] = start_ts
        if end_ts:
            params["endTs"] = end_ts

        return await self._request("GET", endpoint, params=params)

    async def get_device_attributes(
        self,
        device_id: str,
        scope: str | None = None,
        keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get device attributes.

        Args:
            device_id: Device ID
            scope: Attribute scope (SERVER_SCOPE, SHARED_SCOPE, CLIENT_SCOPE), or None for all
            keys: Specific attribute keys to fetch (None for all)

        Returns:
            Attributes as list of {key, value, lastUpdateTs} dicts
        """
        if scope:
            endpoint = f"{Endpoints.TELEMETRY}/{EntityType.DEVICE}/{device_id}/values/attributes/{scope}"
        else:
            # Get all attributes from all scopes
            endpoint = f"{Endpoints.TELEMETRY}/{EntityType.DEVICE}/{device_id}/values/attributes"

        params = {}
        if keys:
            params["keys"] = ",".join(keys)

        result = await self._request("GET", endpoint, params=params if params else None)
        return result if isinstance(result, list) else []

    async def get_device_state(self, device_id: str) -> PranaState:
        """Get current Prana device state.

        This fetches both telemetry and attributes to build a complete state.

        Args:
            device_id: Device ID

        Returns:
            PranaState with current device state
        """
        # Fetch telemetry and attributes in parallel
        telemetry, attributes = await asyncio.gather(
            self.get_device_telemetry(device_id, limit=1),
            self.get_device_attributes(device_id),
        )
        return PranaState.from_telemetry(telemetry, attributes)

    # ==================== RPC (Device Control) ====================

    async def send_rpc_oneway(
        self,
        device_id: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Send one-way RPC command to device (no response expected).

        Args:
            device_id: Device ID
            method: RPC method name
            params: RPC parameters
        """
        await self._request(
            "POST",
            f"{Endpoints.RPC_ONEWAY}/{device_id}",
            json_data={"method": method, "params": params or {}},
        )

    async def send_rpc_twoway(
        self,
        device_id: str,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: int = DEFAULT_RPC_TIMEOUT,
    ) -> Any:
        """Send two-way RPC command to device and wait for response.

        Args:
            device_id: Device ID
            method: RPC method name
            params: RPC parameters
            timeout: RPC timeout in milliseconds

        Returns:
            RPC response data

        Raises:
            RPCError: If RPC command fails
        """
        try:
            return await self._request(
                "POST",
                f"{Endpoints.RPC_TWOWAY}/{device_id}",
                json_data={
                    "method": method,
                    "params": params or {},
                    "timeout": timeout,
                },
            )
        except PranaAPIError as e:
            raise RPCError(f"RPC command '{method}' failed: {e.message}", e.status_code) from e

    # ==================== Prana Device Control ====================

    async def button_click(self, device_id: str, button_number: int) -> None:
        """Simulate button click on device.

        Args:
            device_id: Device ID
            button_number: Button number to click
        """
        await self.send_rpc_oneway(
            device_id,
            "buttonClicked",
            {"buttonNumber": button_number},
        )

    async def rename_device(self, device_id: str, new_name: str) -> None:
        """Rename a device.

        Args:
            device_id: Device ID
            new_name: New device name
        """
        await self.send_rpc_oneway(
            device_id,
            "renameDeviceV2",
            {"deviceName": new_name},
        )

    async def set_auto_heater_temperature(
        self, device_id: str, temperature: int
    ) -> None:
        """Set auto heater temperature.

        Args:
            device_id: Device ID
            temperature: Target temperature
        """
        await self.send_rpc_oneway(
            device_id,
            "setAutoHeaterTemperature",
            {"autoHeaterTemperature": temperature},
        )

    async def set_scenarios(
        self, device_id: str, scenarios: list[dict[str, Any]]
    ) -> None:
        """Set device scenarios.

        Args:
            device_id: Device ID
            scenarios: List of scenario configurations
        """
        await self.send_rpc_oneway(
            device_id,
            "setScenariosV2",
            {"scenarios": scenarios},
        )

    # ==================== Entity Groups ====================

    async def get_entity_groups(
        self,
        entity_type: str = EntityType.DEVICE,
        page: int = 0,
        page_size: int = 100,
    ) -> list[EntityGroup]:
        """Get entity groups.

        Args:
            entity_type: Type of entities in groups
            page: Page number
            page_size: Items per page

        Returns:
            List of entity groups
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }

        data = await self._request(
            "GET",
            f"{Endpoints.ENTITY_GROUPS}/{entity_type}",
            params=params,
        )

        page_data = PageData.from_dict(data, EntityGroup.from_dict)
        return page_data.data

    async def get_group_devices(
        self,
        group_id: str,
        page: int = 0,
        page_size: int = 100,
    ) -> list[Device]:
        """Get devices in an entity group.

        Args:
            group_id: Entity group ID
            page: Page number
            page_size: Items per page

        Returns:
            List of devices in the group
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }

        data = await self._request(
            "GET",
            f"{Endpoints.ENTITY_GROUP}/{group_id}/entities",
            params=params,
        )

        page_data = PageData.from_dict(data, Device.from_dict)
        return page_data.data


# Synchronous wrapper for convenience
class PranaClientSync:
    """Synchronous wrapper for PranaClient.

    This provides a synchronous interface by running the async client
    in an event loop. Useful for simple scripts or non-async contexts.

    Example:
        ```python
        client = PranaClientSync()
        client.login("email@example.com", "password")
        devices = client.get_user_devices()
        client.close()
        ```
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        auto_refresh: bool = True,
    ):
        """Initialize sync client."""
        self._async_client = PranaClient(
            base_url=base_url,
            timeout=timeout,
            auto_refresh=auto_refresh,
        )
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run(self, coro):
        """Run coroutine synchronously."""
        return self._get_loop().run_until_complete(coro)

    def close(self) -> None:
        """Close the client."""
        self._run(self._async_client.close())

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self._async_client.is_authenticated

    def login(self, username: str, password: str) -> TokenPair:
        """Login with username and password."""
        return self._run(self._async_client.login(username, password))

    def logout(self) -> None:
        """Logout."""
        self._run(self._async_client.logout())

    def refresh_token(self) -> TokenPair:
        """Refresh access token."""
        return self._run(self._async_client.refresh_token())

    def get_user(self) -> User:
        """Get current user."""
        return self._run(self._async_client.get_user())

    def get_user_devices(
        self,
        page: int = 0,
        page_size: int = 100,
        text_search: str | None = None,
    ) -> list[Device]:
        """Get user devices."""
        return self._run(
            self._async_client.get_user_devices(page, page_size, text_search)
        )

    def get_device(self, device_id: str) -> Device:
        """Get device by ID."""
        return self._run(self._async_client.get_device(device_id))

    def get_device_state(self, device_id: str) -> PranaState:
        """Get device state."""
        return self._run(self._async_client.get_device_state(device_id))

    def get_device_telemetry(
        self,
        device_id: str,
        keys: list[str] | None = None,
        start_ts: int | None = None,
        end_ts: int | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get device telemetry."""
        return self._run(
            self._async_client.get_device_telemetry(
                device_id, keys, start_ts, end_ts, limit
            )
        )

    def get_device_attributes(
        self,
        device_id: str,
        scope: str | None = None,
        keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get device attributes."""
        return self._run(
            self._async_client.get_device_attributes(device_id, scope, keys)
        )

    def send_rpc_oneway(
        self,
        device_id: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Send one-way RPC."""
        self._run(self._async_client.send_rpc_oneway(device_id, method, params))

    def send_rpc_twoway(
        self,
        device_id: str,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: int = DEFAULT_RPC_TIMEOUT,
    ) -> Any:
        """Send two-way RPC."""
        return self._run(
            self._async_client.send_rpc_twoway(device_id, method, params, timeout)
        )

    def button_click(self, device_id: str, button_number: int) -> None:
        """Click device button."""
        self._run(self._async_client.button_click(device_id, button_number))

    def rename_device(self, device_id: str, new_name: str) -> None:
        """Rename device."""
        self._run(self._async_client.rename_device(device_id, new_name))

    def set_auto_heater_temperature(self, device_id: str, temperature: int) -> None:
        """Set auto heater temperature."""
        self._run(
            self._async_client.set_auto_heater_temperature(device_id, temperature)
        )

    def get_entity_groups(
        self,
        entity_type: str = EntityType.DEVICE,
        page: int = 0,
        page_size: int = 100,
    ) -> list[EntityGroup]:
        """Get entity groups."""
        return self._run(
            self._async_client.get_entity_groups(entity_type, page, page_size)
        )

    def get_group_devices(
        self,
        group_id: str,
        page: int = 0,
        page_size: int = 100,
    ) -> list[Device]:
        """Get devices in group."""
        return self._run(
            self._async_client.get_group_devices(group_id, page, page_size)
        )
