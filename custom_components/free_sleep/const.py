DOMAIN = "free_sleep"
DEFAULT_PORT = 3000
CONF_BASE_URL = "base_url"
CONF_PORT = "port"

API_DEVICE_STATUS = "/api/deviceStatus"
API_SETTINGS = "/api/settings"
API_VITALS_SUMMARY = "/api/metrics/vitals/summary"

PLATFORMS = ["climate", "binary_sensor", "sensor", "button", "switch"]

UPDATE_INTERVAL_SECS_DEFAULT = 15  # fixed internal update cadence

CONF_VITALS_WINDOW_HOURS = "vitals_window_hours"
DEFAULT_VITALS_WINDOW_HOURS = 24
