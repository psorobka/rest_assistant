# Instrukcje pracy z REST Assistant

## Szybki start

- Odpowiadaj po polsku. Nazwy HA, klucze konfiguracji, docstringi i kod zostawiaj
  po angielsku.
- Najpierw sprawdź `git status --short` i `rg --files`. Zachowaj zmiany użytkownika;
  nie zakładaj, że nieśledzone pliki są tymczasowe.
- Zacznij od właściwego wiersza w `docs/agent-workflow.md`. Otwieraj tylko wskazane
  moduły, testy i tłumaczenia; rozszerzaj czytanie, gdy wywołania tego wymagają.
- Kod i testy opisują aktualne zachowanie. README i dokumenty wyjaśniają kontrakty,
  ale nie zastępują implementacji.
- Wdrażaj najmniejszą kompletną zmianę. Nie przenoś ustawień spoza uzgodnionego
  zakresu bez wyraźnej potrzeby.

## Wymagany workflow GitHub

- Każdą zmianę rób na osobnym branchu `codex/<krótki-opis>`; nigdy nie commituj
  ani nie wypychaj bezpośrednio na `main`.
- Dostarczaj zmiany jako Pull Request do `main`.
- Przed scaleniem wymagane joby GitHub Actions muszą być zielone. Naprawiaj
  nieudane joby i czekaj na zielone ponowne uruchomienie; nie kończ pracy ani nie
  scalaj PR, dopóki wymagane kontrole nie przejdą.

## Kontrakty integracji

- `config_flow.py` zapisuje jeden wpis i jedną encję na wpis. Pierwszy krok wybiera
  platformę; pozostałe formularze i platforma encji muszą pozostać zgodne z tym
  wyborem.
- Wspólne pobieranie odpowiedzi należy do `RestCoordinator` w `__init__.py`.
  Platformy `sensor.py` i `binary_sensor.py` prezentują ten sam snapshot i nie
  wykonują osobnych żądań.
- Używaj współdzielonej sesji HA i obsługuj błędy tak, by koordynator oznaczał
  encję jako niedostępną. Nie umieszczaj URL, danych logowania ani payloadu w logach.
- Widoczne teksty dodawaj równolegle do `strings.json`, `translations/en.json` i
  `translations/pl.json`. Zachowuj identyczną strukturę kluczy.
- Nie twórz niezaimplementowanych opcji tylko po to, by odzwierciedlić pełną
  konfigurację wbudowanego REST.

## Weryfikacja

- Na Windows uruchamiaj pytest, Ruff, Node i Playwright w WSL, nie w PowerShell.
- Po zmianie backendu uruchom pytest z coverage i Ruff. Po zmianie config flow lub
  platformy rozważ także Playwright z Dockerem. Nie deklaruj Hassfest/HACS jako
  lokalnie sprawdzonych; workflow uruchamia je w GitHub Actions.
- Testy używają lokalnych atrap endpointu; nie kieruj ich na urządzenia ani usługi
  użytkownika.
- Szczegóły poleceń i mapę plików: `docs/agent-workflow.md`. Zakres pól i format
  zapisanych danych: `docs/configuration-contract.md`.
