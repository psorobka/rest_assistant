import { execFileSync } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { tmpdir } from "node:os";
import { expect, test } from "@playwright/test";

const containerName = `rest-assistant-e2e-${process.pid}`;
const integrationPath = path.resolve("custom_components/rest_assistant");
let configPath;
let baseUrl;
let token;

async function post(route, body = {}) {
  const response = await fetch(`${baseUrl}/${route}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${route}: ${JSON.stringify(result)}`);
  return result;
}

function schemaDefault(flow, name) {
  return flow.data_schema.find((field) => field.name === name)?.default;
}

async function waitForHA() {
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/api/onboarding`, {
        signal: AbortSignal.timeout(2000),
      });
      if (response.ok) return;
    } catch {
      // Wait for the container to finish starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error("Home Assistant did not start");
}

test.beforeAll(async () => {
  test.setTimeout(360_000);
  configPath = await mkdtemp(path.join(tmpdir(), "rest-assistant-ha-e2e-"));
  await mkdir(path.join(configPath, "www"));
  await writeFile(
    path.join(configPath, "www", "status.json"),
    '{"status":"ready","temperature":21.5,"online":true}',
  );
  await writeFile(path.join(configPath, "configuration.yaml"), `
default_config:
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 127.0.0.1
        - 172.16.0.0/12
        - 172.17.0.0/16
      allow_bypass_login: true
    - type: homeassistant
`);
  execFileSync("docker", [
    "run", "--detach", "--name", containerName,
    "--publish", "127.0.0.1::8123",
    "--volume", `${configPath}:/config`,
    "--volume", `${integrationPath}:/config/custom_components/rest_assistant:ro`,
    "homeassistant/home-assistant:stable",
  ], { stdio: "ignore" });
  const port = execFileSync("docker", ["port", containerName, "8123/tcp"], {
    encoding: "utf8",
  }).trim().split(":").at(-1);
  baseUrl = `http://127.0.0.1:${port}`;
  await waitForHA();

  const clientId = `${baseUrl}/`;
  const user = await post("api/onboarding/users", {
    name: "REST Assistant E2E",
    username: `rest_e2e_${process.pid}`,
    password: "temporary-e2e-password-123",
    client_id: clientId,
    language: "pl",
  });
  const form = new FormData();
  form.set("grant_type", "authorization_code");
  form.set("code", user.auth_code);
  form.set("client_id", clientId);
  const authResponse = await fetch(`${baseUrl}/auth/token`, { method: "POST", body: form });
  token = (await authResponse.json()).access_token;
  await post("api/onboarding/core_config");
  await post("api/onboarding/analytics");
  await post("api/onboarding/integration", {
    client_id: clientId,
    redirect_uri: `${baseUrl}/onboarding.html?auth_callback=1`,
  });
});

test.afterAll(async () => {
  try {
    execFileSync("docker", [
      "exec", "--user", "0", containerName, "chmod", "-R", "a+rwX", "/config",
    ], { stdio: "ignore" });
  } catch {
    // The container may not have started.
  }
  try {
    execFileSync("docker", ["rm", "--force", containerName], { stdio: "ignore" });
  } finally {
    if (configPath) await rm(configPath, { recursive: true, force: true });
  }
});

test("REST sensors and rendered template previews work in Home Assistant", async ({ page }) => {
  test.setTimeout(360_000);
  let flow = await post("api/config/config_entries/flow", { handler: "rest_assistant" });
  flow = await post(`api/config/config_entries/flow/${flow.flow_id}`, {
    entity_type: "sensor",
  });
  expect(flow.step_id).toBe("request");
  flow = await post(`api/config/config_entries/flow/${flow.flow_id}`, {
    resource: "http://127.0.0.1:8123/local/status.json",
    method: "GET",
    timeout: 10,
    authentication: "none",
    scan_interval: 60,
  });
  expect(flow.step_id).toBe("entity");

  // Use HA's own in-process endpoint as deterministic response source for the UI smoke check.
  const sensorInput = {
    name: "Example status",
    value_template: "{{ value_json.status }}",
    icon: "mdi:api",
  };
  flow = await post(`api/config/config_entries/flow/${flow.flow_id}`, sensorInput);
  expect(flow.type).toBe("form");
  expect(schemaDefault(flow, "template_preview")).toBe("ready");
  const updatedSensorInput = {
    ...sensorInput,
    value_template: "{{ value_json.temperature }}",
  };
  flow = await post(`api/config/config_entries/flow/${flow.flow_id}`, updatedSensorInput);
  expect(flow.type).toBe("form");
  expect(schemaDefault(flow, "template_preview")).toBe("21.5");
  flow = await post(`api/config/config_entries/flow/${flow.flow_id}`, updatedSensorInput);
  expect(flow.type).toBe("create_entry");

  const statesResponse = await fetch(`${baseUrl}/api/states`, {
    headers: { authorization: `Bearer ${token}` },
  });
  const states = await statesResponse.json();
  expect(states.find((state) => state.entity_id === "sensor.example_status")?.state).toBe(
    "21.5",
  );

  let binaryFlow = await post("api/config/config_entries/flow", {
    handler: "rest_assistant",
  });
  binaryFlow = await post(
    `api/config/config_entries/flow/${binaryFlow.flow_id}`,
    { entity_type: "binary_sensor" },
  );
  binaryFlow = await post(
    `api/config/config_entries/flow/${binaryFlow.flow_id}`,
    {
      resource: "http://127.0.0.1:8123/local/status.json",
      method: "GET",
      timeout: 10,
      authentication: "none",
      scan_interval: 60,
    },
    );
  const binaryInput = {
    name: "Endpoint available",
    value_template: "{{ value_json.status }}",
    device_class: "connectivity",
    payload_on: "ready",
    payload_off: "offline",
  };
  binaryFlow = await post(
    `api/config/config_entries/flow/${binaryFlow.flow_id}`,
    binaryInput,
  );
  expect(binaryFlow.type).toBe("form");
  expect(schemaDefault(binaryFlow, "template_preview")).toBe("ready");
  binaryFlow = await post(
    `api/config/config_entries/flow/${binaryFlow.flow_id}`,
    binaryInput,
  );
  expect(binaryFlow.type).toBe("create_entry");
  const binaryStatesResponse = await fetch(`${baseUrl}/api/states`, {
    headers: { authorization: `Bearer ${token}` },
  });
  const binaryStates = await binaryStatesResponse.json();
  expect(
    binaryStates.find((state) => state.entity_id === "binary_sensor.endpoint_available")
      ?.state,
  ).toBe("on");

  await page.goto(`${baseUrl}/config/integrations`);
  await expect(page.getByText("REST Assistant").first()).toBeVisible({ timeout: 60_000 });
});
