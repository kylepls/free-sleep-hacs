
DOMAIN = "free_sleep"
DEFAULT_PORT = 3000
CONF_BASE_URL = "base_url"
CONF_PORT = "port"

API_DEVICE_STATUS = "/api/deviceStatus"
API_SETTINGS = "/api/settings"
API_VITALS_SUMMARY = "/api/metrics/vitals/summary"

# Platforms
PLATFORMS = ["climate", "binary_sensor", "sensor", "button", "switch"]

# Defaults
UPDATE_INTERVAL_SECS_DEFAULT = 15
VITALS_POLL_SECS_DEFAULT = 900  # 15 minutes
DEFAULT_VITALS_WINDOW_HOURS = 24

# Options
CONF_VITALS_WINDOW_HOURS = "vitals_window_hours"
CONF_UPDATE_INTERVAL_SECS = "update_interval_secs"
CONF_VITALS_MODE = "vitals_mode"                 # "nightly" or "polling"
CONF_VITALS_NIGHTLY_TIME = "vitals_nightly_time" # "HH:MM"
CONF_VITALS_POLL_SECS = "vitals_poll_secs"

VITALS_MODE_NIGHTLY = "nightly"
VITALS_MODE_POLLING = "polling"
