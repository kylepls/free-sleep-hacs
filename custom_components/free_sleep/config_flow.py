from __future__ import annotations
import voluptuous as vol
from typing import Any
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_BASE_URL, CONF_PORT, DEFAULT_PORT,
    CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS,
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
                    options={CONF_VITALS_WINDOW_HOURS: DEFAULT_VITALS_WINDOW_HOURS},
                )
        data_schema = vol.Schema({
            vol.Required(CONF_BASE_URL, description={"suggested_value": "http://localhost"}): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FreeSleepOptionsFlowHandler(config_entry)

class FreeSleepOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_window()

    async def async_step_window(self, user_input=None):
        if user_input is not None:
            hours = int(user_input.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))
            hours = max(1, min(hours, 168))
            return self.async_create_entry(title="", data={CONF_VITALS_WINDOW_HOURS: hours})
        current = self.config_entry.options.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS)
        schema = vol.Schema({ vol.Required(CONF_VITALS_WINDOW_HOURS, default=current): int })
        return self.async_show_form(step_id="window", data_schema=schema)
