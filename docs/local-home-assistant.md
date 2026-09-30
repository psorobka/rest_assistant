# Local Home Assistant demo

This setup runs a separate Home Assistant container for trying REST Assistant.
It does not change the Alerts Assistant container on port `8123`.

- UI: <http://localhost:8124>
- Container: `rest-assistant-ha`
- Config and database: `.ha-dev/config/` (ignored by Git and kept when the
  container is recreated)
- Demo integration: enabled with `demo:` in `configuration.yaml`
- REST Assistant: mounted read-only from this checkout; restart HA after Python
  code changes
- Authentication: trusted-network bypass for loopback and the local Docker
  gateway; the web port is published on `127.0.0.1`, not the LAN

## Start

Run these commands in PowerShell from the repository root. On the first run,
create `.ha-dev/config/configuration.yaml` with the contents below. The existing
demo config also includes this file and a sample JSON response at
`.ha-dev/config/www/status.json`.

```yaml
default_config:
demo:
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 127.0.0.1
        - ::1
        - 172.17.0.1/32
      allow_bypass_login: true
    - type: homeassistant
```

```powershell
$repo = (Get-Location).Path
New-Item -ItemType Directory -Force .ha-dev/config/www | Out-Null
docker run --detach --name rest-assistant-ha --restart unless-stopped `
  --publish 127.0.0.1:8124:8123 `
  --volume "$repo\.ha-dev\config:/config" `
  --volume "$repo\custom_components\rest_assistant:/config/custom_components/rest_assistant:ro" `
  homeassistant/home-assistant:stable
```

On later runs, start the existing container instead:

```powershell
docker start rest-assistant-ha
```

Open <http://localhost:8124>. On a brand-new config, finish the initial HA
onboarding once; after that, trusted-network bypass skips the login screen for
localhost. The built-in Demo integration populates sample devices and sensors.

## Try a REST sensor

The config directory serves `www/status.json` as a local HA resource. Configure
the REST Assistant endpoint URL as:

```text
http://127.0.0.1:8123/local/status.json
```

Use `GET` and a value template such as `{{ value_json.temperature }}`. The
sample response is `{"status":"ready","temperature":21.5,"online":true}`.
For a binary sensor, use `{{ value_json.online }}` and set the on/off payloads to
`True` and `False` (or use a template that returns the configured payloads).

The URL uses port `8123` because the request originates inside the HA container;
the browser-facing host port is `8124`.

## Restart and stop

```powershell
docker restart rest-assistant-ha
docker stop rest-assistant-ha
```

The restart command reloads integration code. Stopping keeps the config and
database. To remove only the container while retaining the demo setup, run
`docker rm -f rest-assistant-ha`, then run the start command again.

The port is bound to localhost deliberately. Do not change it to `0.0.0.0` or
remove the trusted-network restriction for a shared or internet-facing host.
