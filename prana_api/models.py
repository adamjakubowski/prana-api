"""Data models for the Prana API client."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class TokenPair:
    """JWT token pair returned by authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "TokenPair":
        """Create TokenPair from API response."""
        return cls(
            access_token=data.get("token", data.get("accessToken", "")),
            refresh_token=data.get("refreshToken", ""),
            token_type=data.get("tokenType", "Bearer"),
        )


@dataclass
class EntityId:
    """Entity identifier."""

    id: str
    entity_type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityId":
        """Create EntityId from dict."""
        return cls(
            id=data.get("id", ""),
            entity_type=data.get("entityType", ""),
        )


@dataclass
class User:
    """User model."""

    id: EntityId
    email: str
    name: str
    first_name: str
    last_name: str
    authority: str
    customer_id: EntityId | None = None
    tenant_id: EntityId | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)
    created_time: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create User from API response."""
        customer_id = None
        if data.get("customerId"):
            customer_id = EntityId.from_dict(data["customerId"])

        tenant_id = None
        if data.get("tenantId"):
            tenant_id = EntityId.from_dict(data["tenantId"])

        created_time = None
        if data.get("createdTime"):
            created_time = datetime.fromtimestamp(data["createdTime"] / 1000)

        return cls(
            id=EntityId.from_dict(data.get("id", {})),
            email=data.get("email", ""),
            name=data.get("name", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            authority=data.get("authority", ""),
            customer_id=customer_id,
            tenant_id=tenant_id,
            additional_info=data.get("additionalInfo", {}),
            created_time=created_time,
        )


@dataclass
class DeviceCredentials:
    """Device credentials."""

    id: EntityId
    device_id: EntityId
    credentials_type: str
    credentials_id: str
    credentials_value: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceCredentials":
        """Create DeviceCredentials from dict."""
        return cls(
            id=EntityId.from_dict(data.get("id", {})),
            device_id=EntityId.from_dict(data.get("deviceId", {})),
            credentials_type=data.get("credentialsType", ""),
            credentials_id=data.get("credentialsId", ""),
            credentials_value=data.get("credentialsValue"),
        )


@dataclass
class Device:
    """Device model."""

    id: EntityId
    name: str  # Internal name (usually UUID)
    type: str
    label: str | None  # Human-readable name set by user
    device_profile_id: EntityId | None = None
    customer_id: EntityId | None = None
    tenant_id: EntityId | None = None
    device_data: dict[str, Any] = field(default_factory=dict)
    additional_info: dict[str, Any] = field(default_factory=dict)
    created_time: datetime | None = None

    @property
    def device_id(self) -> str:
        """Get the device ID string."""
        return self.id.id

    @property
    def display_name(self) -> str:
        """Get human-readable device name (label if set, otherwise internal name)."""
        if self.label:
            return self.label.strip()
        return self.name

    @property
    def prana_type(self) -> str | None:
        """Get the Prana device model type (e.g., 'Prana 24V 200')."""
        return self.additional_info.get("pranaType")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        """Create Device from API response."""
        device_profile_id = None
        if data.get("deviceProfileId"):
            device_profile_id = EntityId.from_dict(data["deviceProfileId"])

        customer_id = None
        if data.get("customerId"):
            customer_id = EntityId.from_dict(data["customerId"])

        tenant_id = None
        if data.get("tenantId"):
            tenant_id = EntityId.from_dict(data["tenantId"])

        created_time = None
        if data.get("createdTime"):
            created_time = datetime.fromtimestamp(data["createdTime"] / 1000)

        return cls(
            id=EntityId.from_dict(data.get("id", {})),
            name=data.get("name", ""),
            type=data.get("type", ""),
            label=data.get("label"),
            device_profile_id=device_profile_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
            device_data=data.get("deviceData", {}),
            additional_info=data.get("additionalInfo", {}),
            created_time=created_time,
        )


@dataclass
class PranaState:
    """Prana device state from telemetry and attributes.

    Based on actual Prana API response structure.
    """

    # Speed (0-5 display scale, internally 0-50)
    supply_speed: int | None = None  # Incoming air fan speed (0-5)
    extract_speed: int | None = None  # Outgoing air fan speed (0-5)

    # Power and modes (position = 1 means ON, 0 means OFF)
    is_power_on: bool = False  # powerPosition
    is_auto_mode: bool = False  # autoModePosition
    is_bounded_mode: bool = False  # boundedModePosition (linked speeds)
    is_night_mode: bool = False  # nightModePosition
    is_heater_on: bool = False  # heaterPosition

    # Timer
    is_sleep_timer: bool = False  # sleepPosition
    sleep_seconds: int = 0  # sleepSecondsLsb + sleepSecondsMsb

    # Settings
    brightness: int | None = None  # brightnessPosition

    # Sensors
    co2: int | None = None
    voc: int | None = None
    humidity: float | None = None
    temperature: float | None = None  # temperature_2
    pressure: int | None = None

    # Status
    is_online: bool = False  # active attribute
    is_defrosting: bool = False  # defrostingPosition
    wifi_rssi: int | None = None  # wifi signal strength
    firmware_version: int | None = None  # fw_version

    # Last activity
    last_activity_time: datetime | None = None

    # Raw data for any unmapped fields
    raw_telemetry: dict[str, Any] = field(default_factory=dict)
    raw_attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_telemetry(cls, telemetry: dict[str, Any], attributes: dict[str, Any] | None = None) -> "PranaState":
        """Create PranaState from telemetry and attributes data.

        Args:
            telemetry: Telemetry data as {key: [{ts, value}]} format
            attributes: Attributes data as {key: value} or [{key, value}] format
        """
        attributes = attributes or {}

        def get_telemetry_value(key: str) -> Any:
            """Get latest value from telemetry data."""
            if key in telemetry and telemetry[key]:
                values = telemetry[key]
                if isinstance(values, list) and values:
                    val = values[0].get("value") if isinstance(values[0], dict) else values[0]
                    return val
                return values
            return None

        def get_attr_value(key: str) -> Any:
            """Get value from attributes data."""
            # Handle both dict format and list of {key, value} format
            if isinstance(attributes, dict):
                return attributes.get(key)
            elif isinstance(attributes, list):
                for attr in attributes:
                    if attr.get("key") == key:
                        return attr.get("value")
            return None

        def get_value(key: str) -> Any:
            """Get value from telemetry first, then attributes."""
            val = get_telemetry_value(key)
            if val is None:
                val = get_attr_value(key)
            return val

        def get_bool(key: str) -> bool:
            """Get boolean value (position 1 = True, 0 = False)."""
            val = get_value(key)
            if val is None:
                return False
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return val >= 1
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes") or val == "1"
            return bool(val)

        def get_int(key: str) -> int | None:
            val = get_value(key)
            if val is None:
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        def get_float(key: str) -> float | None:
            val = get_value(key)
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Parse last activity time
        last_activity = None
        last_activity_ts = get_attr_value("lastActivityTime")
        if last_activity_ts:
            try:
                last_activity = datetime.fromtimestamp(last_activity_ts / 1000)
            except (ValueError, TypeError, OSError):
                pass

        # Calculate sleep timer seconds from LSB and MSB
        sleep_lsb = get_int("sleepSecondsLsb") or 0
        sleep_msb = get_int("sleepSecondsMsb") or 0
        sleep_seconds = sleep_lsb + (sleep_msb << 8)

        # Convert internal motor speed (0-50) to display speed (0-5)
        # Internal value 10 = display 1, 20 = display 2, etc.
        raw_supply = get_int("motorsSup")
        raw_extract = get_int("motorsExt")
        supply_speed = raw_supply // 10 if raw_supply is not None else None
        extract_speed = raw_extract // 10 if raw_extract is not None else None

        return cls(
            # Speeds - converted to 0-5 display scale
            supply_speed=supply_speed,
            extract_speed=extract_speed,
            # Power and modes
            is_power_on=get_bool("powerPosition"),
            is_auto_mode=get_bool("autoModePosition"),
            is_bounded_mode=get_bool("boundedModePosition"),
            is_night_mode=get_bool("nightModePosition"),
            is_heater_on=get_bool("heaterPosition"),
            # Timer
            is_sleep_timer=get_bool("sleepPosition"),
            sleep_seconds=sleep_seconds,
            # Settings
            brightness=get_int("brightnessPosition"),
            # Sensors
            co2=get_int("co2"),
            voc=get_int("voc"),
            humidity=get_float("humidity"),
            temperature=get_float("temperature_2"),  # Note: temperature_2 is the actual temp
            pressure=get_int("pressure"),
            # Status
            is_online=get_bool("active"),
            is_defrosting=get_bool("defrostingPosition"),
            wifi_rssi=get_int("wifi_rssi"),
            firmware_version=get_int("fw_version"),
            # Last activity
            last_activity_time=last_activity,
            # Raw data
            raw_telemetry=telemetry,
            raw_attributes=attributes if isinstance(attributes, dict) else {a["key"]: a["value"] for a in attributes} if attributes else {},
        )


@dataclass
class PageData:
    """Paginated data response."""

    data: list[Any]
    total_pages: int
    total_elements: int
    has_next: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any], item_factory: Callable | None = None) -> "PageData":
        """Create PageData from API response."""
        items = data.get("data", [])
        if item_factory:
            items = [item_factory(item) for item in items]

        return cls(
            data=items,
            total_pages=data.get("totalPages", 0),
            total_elements=data.get("totalElements", 0),
            has_next=data.get("hasNext", False),
        )


@dataclass
class EntityGroup:
    """Entity group model."""

    id: EntityId
    name: str
    type: str
    owner_id: EntityId | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityGroup":
        """Create EntityGroup from dict."""
        owner_id = None
        if data.get("ownerId"):
            owner_id = EntityId.from_dict(data["ownerId"])

        return cls(
            id=EntityId.from_dict(data.get("id", {})),
            name=data.get("name", ""),
            type=data.get("type", ""),
            owner_id=owner_id,
            additional_info=data.get("additionalInfo", {}),
        )


@dataclass
class Scenario:
    """Prana scenario/schedule model."""

    name: str
    is_active: bool = False
    schedule: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
