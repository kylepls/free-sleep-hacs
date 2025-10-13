
from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, DEFAULT_PORT
from .coordinator import FreeSleepClient, path_join

class FreeSleepConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Validate by calling /api/deviceStatus
            client = FreeSleepClient(self.hass, None, base_url=base_url, port=port)
            try:
                await client.get("/api/deviceStatus")
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                # Unique entry per base_url:port
                await self.async_set_unique_id(f"{base_url}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Free Sleep ({base_url}:{port})",
                    data={CONF_BASE_URL: base_url, CONF_PORT: port},
                )

        data_schema = vol.Schema({
            vol.Required(CONF_BASE_URL, description={"suggested_value": "http://localhost"}): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @callback
    def async_get_options_flow(self, config_entry):
        return FreeSleepOptionsFlow(config_entry)


class FreeSleepOptionsFlow(ConfigFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
