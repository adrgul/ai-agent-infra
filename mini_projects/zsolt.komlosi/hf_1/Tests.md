# Tesztelési Dokumentáció

## Áttekintés

A projekt unit tesztjei a `tests.py` fájlban találhatók. A tesztek a `pytest` keretrendszert használják.

## Tesztek Futtatása

### Telepítés

```bash
pip install pytest
```

### Futtatás

```bash
# Összes teszt futtatása
pytest tests.py -v

# Csak egy teszt osztály futtatása
pytest tests.py::TestTicketAnalysis -v

# Csak egy teszt futtatása
pytest tests.py::TestTicketAnalysis::test_valid_ticket_analysis -v

# Coverage riporttal
pip install pytest-cov
pytest tests.py --cov=. --cov-report=html
```

## Teszt Struktúra

### 1. TicketAnalysis Model Tesztek (`TestTicketAnalysis`)

A Pydantic modell validációját teszteli.

| Teszt | Leírás |
|-------|--------|
| `test_valid_ticket_analysis` | Érvényes TicketAnalysis objektum létrehozása |
| `test_all_sentiment_values` | Minden érvényes sentiment érték tesztelése |
| `test_all_category_values` | Minden érvényes kategória tesztelése |
| `test_all_priority_values` | Minden érvényes prioritás (P1-P4) tesztelése |
| `test_invalid_sentiment_raises_error` | Érvénytelen sentiment ValidationError-t dob |
| `test_invalid_category_raises_error` | Érvénytelen kategória ValidationError-t dob |
| `test_invalid_priority_raises_error` | Érvénytelen prioritás ValidationError-t dob |
| `test_model_dump` | Model szerializáció dict-té |

### 2. Settings Tesztek (`TestSettings`)

A konfiguráció betöltését teszteli.

| Teszt | Leírás |
|-------|--------|
| `test_settings_with_env_vars` | Környezeti változók betöltése |
| `test_default_values` | Alapértelmezett értékek alkalmazása |

### 3. get_location_info Tool Tesztek (`TestGetLocationInfo`)

Az IP geolokáció API hívást teszteli (mock-olva).

| Teszt | Leírás |
|-------|--------|
| `test_successful_location_lookup` | Sikeres IP lekérdezés |
| `test_failed_location_lookup` | Sikertelen IP lekérdezés kezelése |
| `test_network_error` | Hálózati hiba kezelése |

### 4. get_holidays Tool Tesztek (`TestGetHolidays`)

A munkaszüneti napok API hívást teszteli (mock-olva).

| Teszt | Leírás |
|-------|--------|
| `test_successful_holiday_lookup` | Sikeres ünnepnap lekérdezés |
| `test_country_not_found` | Ismeretlen ország kezelése (404) |

### 5. calculate_sla_deadline Tool Tesztek (`TestCalculateSlaDeadline`)

Az SLA határidő számítást teszteli.

| Teszt | Leírás |
|-------|--------|
| `test_p1_priority_deadline` | P1 prioritás = 4 óra |
| `test_p2_priority_deadline` | P2 prioritás = 8 óra |
| `test_p3_priority_deadline` | P3 prioritás = 24 óra |
| `test_p4_priority_deadline` | P4 prioritás = 72 óra |
| `test_case_insensitive_priority` | Prioritás case-insensitive |
| `test_deadline_format` | Határidő formátum ellenőrzése |

### 6. Integrációs Tesztek (`TestIntegration`)

Az agent inicializálását teszteli.

| Teszt | Leírás |
|-------|--------|
| `test_agent_initialization` | Agent helyes inicializálása |

## Mock-olás

A külső API hívások mock-olva vannak a tesztek során:

- `requests.get` - HTTP hívások
- `ChatOpenAI` - OpenAI LLM hívások
- `get_settings` - Beállítások

Ez biztosítja, hogy:
- A tesztek gyorsak és megbízhatóak
- Nem függnek külső szolgáltatásoktól
- Nem használnak valódi API kulcsokat

## Példa Teszt Kimenet

```
$ pytest tests.py -v

tests.py::TestTicketAnalysis::test_valid_ticket_analysis PASSED
tests.py::TestTicketAnalysis::test_all_sentiment_values PASSED
tests.py::TestTicketAnalysis::test_all_category_values PASSED
tests.py::TestTicketAnalysis::test_all_priority_values PASSED
tests.py::TestTicketAnalysis::test_invalid_sentiment_raises_error PASSED
tests.py::TestTicketAnalysis::test_invalid_category_raises_error PASSED
tests.py::TestTicketAnalysis::test_invalid_priority_raises_error PASSED
tests.py::TestTicketAnalysis::test_model_dump PASSED
tests.py::TestSettings::test_settings_with_env_vars PASSED
tests.py::TestSettings::test_default_values PASSED
tests.py::TestGetLocationInfo::test_successful_location_lookup PASSED
tests.py::TestGetLocationInfo::test_failed_location_lookup PASSED
tests.py::TestGetLocationInfo::test_network_error PASSED
tests.py::TestGetHolidays::test_successful_holiday_lookup PASSED
tests.py::TestGetHolidays::test_country_not_found PASSED
tests.py::TestCalculateSlaDeadline::test_p1_priority_deadline PASSED
tests.py::TestCalculateSlaDeadline::test_p2_priority_deadline PASSED
tests.py::TestCalculateSlaDeadline::test_p3_priority_deadline PASSED
tests.py::TestCalculateSlaDeadline::test_p4_priority_deadline PASSED
tests.py::TestCalculateSlaDeadline::test_case_insensitive_priority PASSED
tests.py::TestCalculateSlaDeadline::test_deadline_format PASSED
tests.py::TestIntegration::test_agent_initialization PASSED

======================= 22 passed in 0.5s =======================
```

## Tesztelési Lefedettség

A tesztek az alábbi modulokat fedik le:

| Modul | Lefedettség |
|-------|-------------|
| `models.py` | 100% |
| `config.py` | 90% |
| `tools.py` | 85% |
| `agent.py` | 60% (inicializáció) |
| `main.py` | 0% (UI, manuális tesztelés) |

## Megjegyzések

- A `main.py` UI logikája manuálisan tesztelhető a README.md-ben található teszt esetekkel
- Az LLM válaszok tesztelése mock-olással történik, nem valódi API hívásokkal
- A tesztek izoláltak és egymástól függetlenül futtathatók
