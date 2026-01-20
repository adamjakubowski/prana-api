"""Constants for the Prana API client."""

# Base URL for the Prana IoT API
BASE_URL = "https://iot.sensesaytech.com"

# API Endpoints
class Endpoints:
    """API endpoint paths."""

    # Authentication
    AUTH_LOGIN = "/api/auth/login"
    AUTH_TOKEN = "/api/auth/token"
    AUTH_LOGOUT = "/api/auth/logout"
    AUTH_CHANGE_PASSWORD = "/api/auth/changePassword"

    # No-auth endpoints
    NOAUTH_SIGNUP = "/api/noauth/signup"
    NOAUTH_ACTIVATE = "/api/noauth/activateByEmailCode"
    NOAUTH_RESEND_ACTIVATION = "/api/noauth/resendEmailActivation"
    NOAUTH_RESET_PASSWORD_REQUEST = "/api/noauth/resetPasswordByEmail"
    NOAUTH_RESET_PASSWORD = "/api/noauth/resetPassword"
    NOAUTH_OAUTH2_CLIENTS = "/api/noauth/oauth2Clients"

    # User
    AUTH_USER = "/api/auth/user"
    USER_DEVICES = "/api/customer/devices"

    # Customer
    CUSTOMER = "/api/customer"

    # Device
    DEVICE = "/api/device"

    # Entity Groups
    ENTITY_GROUP = "/api/entityGroup"
    ENTITY_GROUPS = "/api/entityGroups"

    # RPC
    RPC_ONEWAY = "/api/rpc/oneway"
    RPC_TWOWAY = "/api/rpc/twoway"

    # Telemetry
    TELEMETRY = "/api/plugins/telemetry"

    # Rule Engine
    RULE_ENGINE = "/api/rule-engine"


# Device attribute scopes
class AttributeScope:
    """Attribute scope types."""

    SERVER_SCOPE = "SERVER_SCOPE"
    SHARED_SCOPE = "SHARED_SCOPE"
    CLIENT_SCOPE = "CLIENT_SCOPE"


# Entity types
class EntityType:
    """Entity types in ThingsBoard."""

    DEVICE = "DEVICE"
    USER = "USER"
    CUSTOMER = "CUSTOMER"
    ENTITY_GROUP = "ENTITY_GROUP"


# RPC Methods for Prana devices
class RPCMethod:
    """Known RPC methods for Prana device control."""

    BUTTON_CLICKED = "buttonClicked"
    RENAME_DEVICE = "renameDeviceV2"
    SET_AUTO_HEATER_TEMP = "setAutoHeaterTemperature"
    SET_SCENARIOS = "setScenariosV2"
    SET_FIRMWARE = "setFw"


# Button numbers for Prana device control
# These map to physical/virtual buttons on the device.
# The device is controlled by sending buttonClicked RPC with a buttonNumber.
class ButtonNumber:
    """Known button numbers for Prana device control.

    These button numbers are used with the buttonClicked RPC method.
    Some mappings may vary by device model or firmware version.
    """

    # Power control
    POWER = 1  # Toggle power on/off

    # Speed control (global - affects both fans in bounded mode)
    SPEED_UP = 2  # Increase fan speed
    SPEED_DOWN = 3  # Decrease fan speed

    # Mode toggles
    NIGHT_MODE = 4  # Toggle night mode
    AUTO_MODE = 5  # Toggle auto mode
    HEATER = 6  # Toggle heater (winter mode)
    BOUNDED_MODE = 7  # Toggle bounded mode (link/unlink supply and extract fans)

    # Individual fan control (when bounded mode is OFF)
    # These buttons control supply and extract fans independently
    SUPPLY_SPEED_UP = 8  # Increase supply (incoming) fan speed
    SUPPLY_SPEED_DOWN = 9  # Decrease supply (incoming) fan speed
    EXTRACT_SPEED_UP = 10  # Increase extract (outgoing) fan speed
    EXTRACT_SPEED_DOWN = 11  # Decrease extract (outgoing) fan speed

    # Timer/Sleep
    SLEEP_TIMER = 12  # Toggle or cycle sleep timer

    # Display
    BRIGHTNESS = 13  # Cycle display brightness


# Device state keys (actual API keys from Prana/ThingsBoard)
class DeviceStateKey:
    """Known device telemetry/attribute keys."""

    # Speed (telemetry) - internal values 0-50, display as 0-5 (divide by 10)
    MOTORS_SUPPLY = "motorsSup"  # Supply/incoming motor speed (internal 0-50)
    MOTORS_EXTRACT = "motorsExt"  # Extract/outgoing motor speed (internal 0-50)

    # Power and modes (telemetry/attributes - position values: 1=ON, 0=OFF)
    POWER_POSITION = "powerPosition"
    AUTO_MODE_POSITION = "autoModePosition"
    BOUNDED_MODE_POSITION = "boundedModePosition"  # Linked supply/extract speeds
    NIGHT_MODE_POSITION = "nightModePosition"
    HEATER_POSITION = "heaterPosition"
    DEFROSTING_POSITION = "defrostingPosition"

    # Timer (attributes)
    SLEEP_POSITION = "sleepPosition"
    SLEEP_SECONDS_LSB = "sleepSecondsLsb"
    SLEEP_SECONDS_MSB = "sleepSecondsMsb"

    # Settings (attributes)
    BRIGHTNESS_POSITION = "brightnessPosition"

    # Sensors (telemetry)
    CO2 = "co2"
    VOC = "voc"
    HUMIDITY = "humidity"
    TEMPERATURE = "temperature_2"  # Note: actual key is temperature_2
    PRESSURE = "pressure"

    # Status (attributes)
    ACTIVE = "active"  # Whether device is online
    LAST_ACTIVITY_TIME = "lastActivityTime"
    WIFI_RSSI = "wifi_rssi"
    FIRMWARE_VERSION = "fw_version"

    # Device info (attributes)
    CONFIG = "config"
    STATE = "state"
    MAC = "mac"


# Sleep timer options (in minutes)
SLEEP_TIMER_OPTIONS = [10, 20, 30, 60, 90, 120, 180, 300, 540]

# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT = 30

# Default timeout for RPC requests (milliseconds)
DEFAULT_RPC_TIMEOUT = 10000
