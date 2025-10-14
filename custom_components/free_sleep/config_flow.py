
from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_PORT,
    DEFAULT_PORT,
    CONF_VITALS_WINDOW_HOURS,
    DEFAULT_VITALS_WINDOW_HOURS,
    CONF_UPDATE_INTERVAL_SECS,
    UPDATE_INTERVAL_SECS_DEFAULT,
    CONF_VITALS_MODE,
    VITALS_MODE_NIGHTLY,
    VITALS_MODE_POLLING,
    CONF_VITALS_NIGHTLY_TIME,
    CONF_VITALS_POLL_SECS,
    VITALS_POLL_SECS_DEFAULT,
)
from .coordinator import FreeSleepClient

class FreeSleepConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            client = FreeSleepClient(self.hass, None, base_url=base_url, port=port)
            try:
                await client.get("/api/deviceStatus")
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(f"{base_url}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Free Sleep ({base_url}:{port})",
                    data={CONF_BASE_URL: base_url, CONF_PORT: port},
                    options={
                        CONF_VITALS_WINDOW_HOURS: DEFAULT_VITALS_WINDOW_HOURS,
                        CONF_UPDATE_INTERVAL_SECS: UPDATE_INTERVAL_SECS_DEFAULT,
                        CONF_VITALS_MODE: VITALS_MODE_POLLING,
                        CONF_VITALS_NIGHTLY_TIME: "02:00",
                        CONF_VITALS_POLL_SECS: VITALS_POLL_SECS_DEFAULT,
                    },
                )

        data_schema = vol.Schema({
            vol.Required(CONF_BASE_URL, description={"suggested_value": "http://localhost"}): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @callback
    def async_get_options_flow(self, config_entry):
        return FreeSleepOptionsFlowHandler(config_entry)

class FreeSleepOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_general()

    async def async_step_general(self, user_input=None):
        if user_input is not None:
            # Validate and persist
            hours = int(user_input.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))
            hours = max(1, min(hours, 168))

            interval = int(user_input.get(CONF_UPDATE_INTERVAL_SECS, UPDATE_INTERVAL_SECS_DEFAULT))
            interval = max(5, min(interval, 3600))

            mode = user_input.get(CONF_VITALS_MODE, VITALS_MODE_POLLING)
            if mode not in (VITALS_MODE_POLLING, VITALS_MODE_NIGHTLY):
                mode = VITALS_MODE_POLLING

            nightly_time = user_input.get(CONF_VITALS_NIGHTLY_TIME, "02:00")
            if not isinstance(nightly_time, str) or ":" not in nightly_time:
                nightly_time = "02:00"

            poll_secs = int(user_input.get(CONF_VITALS_POLL_SECS, VITALS_POLL_SECS_DEFAULT))
            poll_secs = max(15, min(poll_secs, 86400))

            return self.async_create_entry(title="", data={
                CONF_VITALS_WINDOW_HOURS: hours,
                CONF_UPDATE_INTERVAL_SECS: interval,
                CONF_VITALS_MODE: mode,
                CONF_VITALS_NIGHTLY_TIME: nightly_time,
                CONF_VITALS_POLL_SECS: poll_secs,
            })

        opts = self.config_entry.options
        schema = vol.Schema({
            vol.Required(CONF_VITALS_WINDOW_HOURS, default=opts.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS)): int,
            vol.Required(CONF_UPDATE_INTERVAL_SECS, default=opts.get(CONF_UPDATE_INTERVAL_SECS, UPDATE_INTERVAL_SECS_DEFAULT)): int,
            vol.Required(CONF_VITALS_MODE, default=opts.get(CONF_VITALS_MODE, VITALS_MODE_POLLING)): vol.In([VITALS_MODE_POLLING, VITALS_MODE_NIGHTLY]),
            vol.Required(CONF_VITALS_NIGHTLY_TIME, default=opts.get(CONF_VITALS_NIGHTLY_TIME, "02:00")): str,
            vol.Required(CONF_VITALS_POLL_SECS, default=opts.get(CONF_VITALS_POLL_SECS, VITALS_POLL_SECS_DEFAULT)): int,
        })
        return self.async_show_form(step_id="general", data_schema=schema)
