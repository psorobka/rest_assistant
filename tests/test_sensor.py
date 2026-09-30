"""Entity and coordinator setup tests."""

import pytest
from aioresponses import aioresponses
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rest_assistant.const import DOMAIN

ENDPOINT = "http://rest-test.local/status"


def make_entry(entity_type: str, payload_off: str = "OFF") -> MockConfigEntry:
    """Build a representative config entry."""
    data = {
        "entity_type": entity_type,
        "resource": ENDPOINT,
        "method": "GET",
        "timeout": 10,
        "authentication": "none",
        "scan_interval": 60,
        "name": "Test status",
        "value_template": (
            "{{ value_json.temperature }}"
            if entity_type == "sensor"
            else "{{ value_json.state }}"
        ),
    }
    if entity_type == "sensor":
        data.update({"unit_of_measurement": "°C", "icon": "mdi:thermometer"})
    else:
        data.update({"payload_on": "on", "payload_off": payload_off})
    return MockConfigEntry(
        domain=DOMAIN, title="Test REST", unique_id=ENDPOINT, data=data
    )


@pytest.mark.parametrize(
    ("entity_type", "expected_state"), [("sensor", "on"), ("binary_sensor", "on")]
)
async def test_entry_creates_selected_sensor(hass, entity_type, expected_state):
    """The entry creates the chosen platform entity and reads JSON state."""
    entry = make_entry(entity_type)
    entry.add_to_hass(hass)
    payload = {"temperature": 21.5} if entity_type == "sensor" else {"state": "on"}
    with aioresponses() as mocked:
        mocked.get(ENDPOINT, payload=payload, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_id = f"{entity_type}.test_status"
    if entity_type == "sensor":
        assert hass.states.get(entity_id).state == "21.5"
    else:
        assert hass.states.get(entity_id).state == expected_state
        assert hass.states.get("sensor.test_status") is None
    if entity_type == "sensor":
        assert hass.states.get(entity_id).attributes["unit_of_measurement"] == "°C"
        assert hass.states.get(entity_id).attributes["icon"] == "mdi:thermometer"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_binary_sensor_off_payload(hass):
    """The binary sensor maps its configured off payload to off."""
    entry = make_entry("binary_sensor", payload_off="off")
    entry.add_to_hass(hass)
    with aioresponses() as mocked:
        mocked.get(ENDPOINT, payload={"state": "off"}, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.test_status").state == "off"
