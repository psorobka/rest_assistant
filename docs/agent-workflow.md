# Mapa pracy nad integracją

Użyj tabeli, by przejść od zgłoszenia do właściwego kodu i testu bez czytania całego
repozytorium.

| Obszar | Kod i zasoby | Testy |
| --- | --- | --- |
| Config flow, walidacja URL, credentials, metody | `custom_components/rest_assistant/config_flow.py`, `strings.json`, `translations/*.json` | `tests/test_config_flow.py`, `tests/test_translations.py` |
| Pobieranie REST, timeout, auth, setup/unload | `custom_components/rest_assistant/__init__.py`, `const.py` | `tests/test_sensor.py` |
| Encja liczbowego/tekstowego sensora | `custom_components/rest_assistant/sensor.py` | `tests/test_sensor.py` |
| Binary sensor i mapowanie stanów | `custom_components/rest_assistant/binary_sensor.py` | `tests/test_sensor.py` |
| Flow i widok w rzeczywistym HA | `tests/e2e/ha-rest.e2e.spec.mjs`, `playwright.ha.config.mjs` | Playwright uruchamia odizolowany kontener HA |
| Jakość i CI | `.github/workflows/ci.yml`, `requirements_*.txt`, `package*.json` | osobne joby Ruff, pytest, Playwright, Hassfest i HACS |

## Polecenia lokalne w WSL

Z katalogu repozytorium:

```sh
ruff check .
ruff format --check .
pytest -q --cov=custom_components/rest_assistant --cov-report=term-missing --cov-fail-under=80
npm ci
npm run test:ha
```

Pierwsze uruchomienie Playwright wymaga `npx playwright install --with-deps chromium`
i działającego Dockera. Testy HA używają lokalnego JSON w katalogu tymczasowym.

Na Windows uruchamiaj powyższe komendy przez WSL, np.:

```powershell
wsl.exe -e sh -lc 'cd /mnt/c/Users/<user>/Documents/ChatGPT/rest_assistant && pytest -q'
```

W razie problemu ze środowiskiem sprawdź `python3 --version`, `node --version` i
`docker version` w WSL. Testy projektu zostały zweryfikowane z HA z fixture
`pytest-homeassistant-custom-component`; Docker E2E pobiera obraz Home Assistant
`stable`.

## Uwaga o zakresie E2E

Playwright uruchamia flow przez API HA, sprawdza utworzone encje i otwiera widok
integracji w przeglądarce. Nie automatyzuje jeszcze wpisywania danych w formularze
flow przez kliknięcia. Testy pytest pokrywają kroki formularza, walidację i błędy.
