"""Constants for REST Assistant."""

from homeassistant.const import Platform

DOMAIN = "rest_assistant"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_ENTITY_TYPE = "entity_type"
CONF_AUTHENTICATION = "authentication"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VALUE_TEMPLATE = "value_template"
CONF_UNIT = "unit_of_measurement"
CONF_DEVICE_CLASS = "device_class"
CONF_ICON = "icon"
CONF_PAYLOAD_ON = "payload_on"
CONF_PAYLOAD_OFF = "payload_off"
