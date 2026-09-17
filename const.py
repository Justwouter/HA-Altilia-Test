from homeassistant.const import Platform


DOMAIN = "altilia"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30 # Refresh rate according to docs

STATUS_PATH = "/api/v1/state"
INFO_PATH = "/api/v1/info"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

ATTR_FAULTS = "faults"
