"""REST binary sensor platform."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_TYPE,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the REST binary sensor entity."""
    if entry.data[CONF_ENTITY_TYPE] != "binary_sensor":
        return
    async_add_entities(
        [RestValueBinarySensor(hass.data[DOMAIN][entry.entry_id], entry)]
    )


class RestValueBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor with configurable on/off payloads."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config = entry.data
        self._attr_unique_id = entry.unique_id
        self._attr_name = self._config[CONF_NAME]
        try:
            self._attr_device_class = BinarySensorDeviceClass(
                self._config.get(CONF_DEVICE_CLASS)
            )
        except (ValueError, TypeError):
            pass
        self._template = Template(self._config[CONF_VALUE_TEMPLATE], coordinator.hass)

    @property
    def is_on(self) -> bool | None:
        """Compare rendered response with configured on/off values."""
        try:
            value = self._template.async_render(
                {"value_json": self.coordinator.data, "value": self.coordinator.data},
                parse_result=False,
            )
        except (ValueError, TypeError):
            return None
        if value == self._config.get(CONF_PAYLOAD_ON, "ON"):
            return True
        if value == self._config.get(CONF_PAYLOAD_OFF, "OFF"):
            return False
        return None
