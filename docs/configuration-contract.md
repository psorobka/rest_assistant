# Kontrakt konfiguracji

To opis obecnej implementacji, nie pełnej listy ustawień wbudowanej integracji
REST Home Assistant.

## Przepływ

1. Użytkownik wybiera `sensor` albo `binary_sensor`.
2. Wspólny formularz zbiera `resource`, `method`, `timeout`, `authentication` i
   `scan_interval`.
3. Osobny krok zbiera `payload` dla POST oraz `username` i `password` dla Basic lub
   Digest. Flow sprawdza endpoint, zanim pozwoli utworzyć wpis.
4. Formularz encji zbiera `name` i `value_template`, a następnie pola platformy:
   - Sensor: `unit_of_measurement`, `device_class`, `icon`.
   - Binary Sensor: `device_class`, `payload_on`, `payload_off`.
5. Pierwsze zatwierdzenie formularza renderuje szablon na odpowiedzi zapamiętanej
   podczas sprawdzania endpointu. Wynik pojawia się w polu tylko do odczytu. Można
   poprawić szablon i zatwierdzić formularz ponownie, aby odświeżyć wynik; kolejne
   zatwierdzenie bez zmian zapisuje encję.

`value_template` otrzymuje zmienne `value_json` i `value`. Odpowiedź HTTP jest
interpretowana jako JSON, jeśli się parsuje; w przeciwnym razie jako tekst. Podgląd
korzysta z jednorazowej odpowiedzi pobranej w kroku żądania, a nie z kolejnego
odpytywania endpointu.

## Cykl życia i dane

- Każdy config entry tworzy jedną encję. Można skonfigurować wiele encji z tym
  samym endpointem, jeśli różnią się platformą lub nazwą.
- Unique ID składa się z platformy, znormalizowanego endpointu i znormalizowanej
  nazwy. Zmiana nazwy w nowym wpisie oznacza inną tożsamość wpisu.
- Koordynator wykonuje wspólne odpytywanie według `scan_interval`. Błąd pierwszego
  pobrania opóźnia setup; błąd kolejnych odczytów zgłasza stan niedostępny przez
  mechanizm koordynatora.
- Uwierzytelnianie obsługuje Basic i Digest. Ustawienia i dane logowania są
  przechowywane w danych config entry HA; błędy integracji nie wypisują ich do logu.
- Binary Sensor porównuje wynik szablonu dokładnie z `payload_on` i `payload_off`.
  Inna wartość daje stan nieznany.

## Poza obecnym zakresem

Brak konfiguracji nagłówków i parametrów URL, `resource_template`, ustawień SSL,
kodowania, ścieżki/atrybutów JSON, REST Binary Sensor opartych o wiele sensorów na
wspólnym żądaniu, wielu encji w jednym wpisie, reconfigure/options flow i importu
YAML. Rozszerzając ten zakres, aktualizuj config flow, platformę, tłumaczenia,
testy i tę dokumentację razem.
