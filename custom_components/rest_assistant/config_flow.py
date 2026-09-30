"""Config flow for REST Assistant."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_METHOD,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCE,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_AUTHENTICATION,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)


class RestAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one sensor from a REST endpoint."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Choose entity type, then configure its request and state."""
        if user_input is not None:
            self._data = {CONF_ENTITY_TYPE: user_input[CONF_ENTITY_TYPE]}
            return await self.async_step_request()
        polish = self.hass.config.language.startswith("pl")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENTITY_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": "sensor",
                                    "label": "Czujnik" if polish else "Sensor",
                                },
                                {
                                    "value": "binary_sensor",
                                    "label": (
                                        "Czujnik binarny" if polish else "Binary sensor"
                                    ),
                                },
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_request(self, user_input: dict[str, Any] | None = None):
        """Configure endpoint, method, authentication type, and timing."""
        errors = {}
        if user_input is not None:
            parsed = urlparse(user_input[CONF_RESOURCE])
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors[CONF_RESOURCE] = "invalid_url"
            else:
                self._data.update(user_input)
                if (
                    user_input[CONF_METHOD] == "POST"
                    or user_input[CONF_AUTHENTICATION] != "none"
                ):
                    return await self.async_step_request_details()
                try:
                    await self._validate_endpoint(self._data)
                except (aiohttp.ClientError, TimeoutError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_entity()
        return self.async_show_form(
            step_id="request",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RESOURCE): str,
                    vol.Required(CONF_METHOD, default="GET"): vol.In(["GET", "POST"]),
                    vol.Required(CONF_TIMEOUT, default=10): vol.All(
                        int, vol.Range(min=1, max=300)
                    ),
                    vol.Required(CONF_AUTHENTICATION, default="none"): vol.In(
                        ["none", "basic", "digest"]
                    ),
                    vol.Required(CONF_SCAN_INTERVAL, default=30): vol.All(
                        int, vol.Range(min=5, max=86400)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_request_details(
        self, user_input: dict[str, Any] | None = None
    ):
        """Collect request body or credentials only when selected above."""
        errors = {}
        schema = {}
        if self._data[CONF_METHOD] == "POST":
            schema[vol.Required("payload")] = str
        if self._data[CONF_AUTHENTICATION] != "none":
            schema[vol.Required(CONF_USERNAME)] = str
            schema[vol.Required(CONF_PASSWORD)] = str
        if user_input is not None:
            self._data.update(user_input)
            if self._data[CONF_METHOD] == "POST" and not self._data["payload"]:
                errors["base"] = "payload_required"
            elif not all(
                self._data.get(key)
                for key in (CONF_USERNAME, CONF_PASSWORD)
                if self._data[CONF_AUTHENTICATION] != "none"
            ):
                errors["base"] = "credentials_required"
            else:
                try:
                    await self._validate_endpoint(self._data)
                except (aiohttp.ClientError, TimeoutError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_entity()
        return self.async_show_form(
            step_id="request_details", data_schema=vol.Schema(schema), errors=errors
        )

    async def _validate_endpoint(self, data: dict[str, Any]) -> None:
        """Make a request to verify the endpoint and credentials."""
        kwargs: dict[str, Any] = {
            "timeout": aiohttp.ClientTimeout(total=data[CONF_TIMEOUT])
        }
        if data[CONF_AUTHENTICATION] == "basic":
            kwargs["auth"] = aiohttp.BasicAuth(data[CONF_USERNAME], data[CONF_PASSWORD])
        elif data[CONF_AUTHENTICATION] == "digest":
            kwargs["middlewares"] = (
                aiohttp.DigestAuthMiddleware(data[CONF_USERNAME], data[CONF_PASSWORD]),
            )
        if data[CONF_METHOD] == "POST":
            kwargs["data"] = data.get("payload")
        request = getattr(async_get_clientsession(self.hass), data[CONF_METHOD].lower())
        async with request(data[CONF_RESOURCE], **kwargs) as response:
            response.raise_for_status()

    async def async_step_entity(self, user_input: dict[str, Any] | None = None):
        """Configure selected entity platform."""
        entity_type = self._data[CONF_ENTITY_TYPE]
        if user_input is not None:
            self._data.update(user_input)
            unique_id = ":".join(
                (
                    self._data[CONF_ENTITY_TYPE],
                    self._data[CONF_RESOURCE].strip().casefold(),
                    self._data[CONF_NAME].strip().casefold(),
                )
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        schema: dict[Any, Any] = {
            vol.Required(CONF_NAME): str,
            vol.Optional(CONF_VALUE_TEMPLATE, default="{{ value_json }}"): str,
        }
        if entity_type == "sensor":
            schema.update(
                {
                    vol.Optional(CONF_UNIT): str,
                    vol.Optional(CONF_DEVICE_CLASS): _device_class_selector(
                        SensorDeviceClass
                    ),
                    vol.Optional(CONF_ICON): str,
                }
            )
        else:
            schema.update(
                {
                    vol.Optional(CONF_DEVICE_CLASS): _device_class_selector(
                        BinarySensorDeviceClass
                    ),
                    vol.Optional(CONF_PAYLOAD_ON, default="ON"): str,
                    vol.Optional(CONF_PAYLOAD_OFF, default="OFF"): str,
                }
            )
        return self.async_show_form(step_id="entity", data_schema=vol.Schema(schema))


def _device_class_selector(device_classes):
    """Build a dropdown from a platform device-class enum."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": item.value, "label": item.value.replace("_", " ").title()}
                for item in device_classes
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
