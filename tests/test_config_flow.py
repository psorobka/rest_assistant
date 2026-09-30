"""Config flow coverage."""

from aioresponses import aioresponses
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.rest_assistant.const import DOMAIN


async def test_flow_starts_with_entity_type_choice(hass):
    """The first step asks whether to create a sensor or binary sensor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    field = next(iter(result["data_schema"].schema.values()))
    assert {item["value"] for item in field.config["options"]} == {
        "sensor",
        "binary_sensor",
    }


async def test_invalid_resource_is_rejected(hass):
    """Only HTTP(S) endpoints are accepted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "sensor"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "resource": "file:///etc/passwd",
            "method": "GET",
            "timeout": 10,
            "authentication": "none",
            "scan_interval": 30,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["resource"] == "invalid_url"


async def test_post_requires_payload(hass):
    """POST cannot be saved without a request body."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "binary_sensor"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "resource": "http://example.test/state",
            "method": "POST",
            "timeout": 10,
            "authentication": "none",
            "scan_interval": 30,
        },
    )
    assert result["step_id"] == "request_details"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"payload": ""}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "payload_required"


async def test_request_schema_has_selected_method_and_auth_options(hass):
    """The request step offers GET/POST and none/basic/digest auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "sensor"}
    )
    fields = result["data_schema"].schema
    method = next(value for key, value in fields.items() if key.schema == "method")
    authentication = next(
        value for key, value in fields.items() if key.schema == "authentication"
    )
    assert method.container == ["GET", "POST"]
    assert authentication.container == ["none", "basic", "digest"]


async def test_sensor_flow_creates_entry_after_endpoint_check(hass):
    """A checked endpoint and sensor form complete the config flow."""
    endpoint = "http://rest-test.local/temperature"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "sensor"}
    )
    with aioresponses() as mocked:
        mocked.get(endpoint, payload={"temperature": 21.5}, repeat=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "resource": endpoint,
                "method": "GET",
                "timeout": 10,
                "authentication": "none",
                "scan_interval": 60,
            },
        )
        assert result["step_id"] == "entity"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Temperature",
                "value_template": "{{ value_json.temperature }}",
                "unit_of_measurement": "°C",
                "icon": "mdi:thermometer",
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].data["resource"] == endpoint


async def test_authentication_requires_credentials(hass):
    """Basic and digest auth cannot be submitted without both credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "sensor"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "resource": "http://rest-test.local/state",
            "method": "GET",
            "timeout": 10,
            "authentication": "basic",
            "scan_interval": 30,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "", "password": ""}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "credentials_required"


async def test_endpoint_http_error_is_shown_in_flow(hass):
    """HTTP failures keep the user in the request step."""
    endpoint = "http://rest-test.local/unavailable"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_type": "binary_sensor"}
    )
    with aioresponses() as mocked:
        mocked.get(endpoint, status=503)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "resource": endpoint,
                "method": "GET",
                "timeout": 10,
                "authentication": "none",
                "scan_interval": 60,
            },
        )
    assert result["step_id"] == "request"
    assert result["errors"]["base"] == "cannot_connect"
