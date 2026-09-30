"""REST sensor platforms."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RestCoordinator
from .const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the REST sensor entity."""
    if entry.data[CONF_ENTITY_TYPE] != "sensor":
        return
    async_add_entities([RestValueSensor(hass.data[DOMAIN][entry.entry_id], entry)])


class RestValueSensor(CoordinatorEntity, SensorEntity):
    """Sensor with a templated state from a shared REST response."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RestCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._config = entry.data
        self._attr_unique_id = entry.unique_id
        self._attr_name = self._config[CONF_NAME]
        self._attr_native_unit_of_measurement = self._config.get(CONF_UNIT)
        self._attr_icon = self._config.get(CONF_ICON)
        device_class = self._config.get(CONF_DEVICE_CLASS)
        try:
            self._attr_device_class = SensorDeviceClass(device_class)
        except (ValueError, TypeError):
            pass
        self._template = Template(self._config[CONF_VALUE_TEMPLATE], coordinator.hass)

    @property
    def native_value(self) -> Any:
        """Render the configured template against the last HTTP response."""
        return self._render()

    def _render(self) -> str | None:
        payload = self.coordinator.data
        try:
            return self._template.async_render(
                {"value_json": payload, "value": payload}, parse_result=False
            )
        except (ValueError, TypeError):
            return None
