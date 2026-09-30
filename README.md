# REST Assistant

Home Assistant custom integration for configuring REST sensors from the UI.
Current release: **1.0.0**.
The first step lets you choose a regular sensor or a binary sensor. Each config
entry creates one entity; separate entries can share an endpoint when their
entity names differ.

## Included settings

- Endpoint URL, GET/POST, timeout, authentication type, and polling interval.
- POST payload and Basic/Digest credentials appear in a follow-up form only
  when the selected method or authentication needs them.
- Value template for either entity type.
- Sensor unit, device class, and icon.
- Binary sensor device class and on/off values.
- Endpoint and credentials are checked before creating the entry. HTTP errors
  and connection failures are reported in the flow.

Headers, query parameters, SSL options, JSON attributes, resource templates,
multiple entities per request, and other advanced native REST options are not
part of this initial scope.

## Installation

In HACS, open **Integrations → Custom repositories**, add
`https://github.com/psorobka/rest_assistant` as an **Integration**, install
**REST Assistant**, then restart Home Assistant. After it starts, add the
integration from **Settings → Devices & services → Add integration**.

For manual installation, copy `custom_components/rest_assistant` into the
`custom_components` directory of the Home Assistant configuration, then restart
Home Assistant.

## Development and verification in WSL

Use Python 3.13 or later, Node.js 22, Docker, and Chromium in WSL:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements_test.txt
ruff check .
ruff format --check .
pytest -q --cov=custom_components/rest_assistant --cov-report=term-missing --cov-fail-under=80
npm ci
npx playwright install --with-deps chromium
npm run test:ha
```

The Playwright suite starts an isolated Home Assistant container and a
temporary configuration. It drives both config flows against a local JSON
resource, checks the created entity states, and verifies the rendered
integration page. Hassfest and HACS validation run in GitHub Actions.

Contributor shortcuts: [agent workflow map](docs/agent-workflow.md),
[configuration contract](docs/configuration-contract.md), and [project
instructions](AGENTS.md).
