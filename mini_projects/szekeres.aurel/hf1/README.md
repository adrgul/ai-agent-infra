# HF1 - Publikus API Meghívása Pythonból

## Gyors Kezdés

### 1. Telepítés

```bash
cd hf1
pip install -r requirements.txt
```

### 2. Futtatás

```bash
python src/main.py
```

### 3. Interakció

```
🤖 > weather Budapest
🤖 > timezone Paris
🤖 > country Hungary
🤖 > location Statue of Liberty
🤖 > exit
```

---

## Projekt Szerkezete

```
hf1/
├── src/
│   ├── __init__.py          # Python package
│   ├── main.py              # Entry point - interaktív hurok
│   ├── agent.py             # Mini-agent logika (input parsing)
│   ├── api_clients.py       # API hívások (requests library)
│   └── formatters.py        # Output formázás
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── README.md                # Ez a fájl
└── ASSIGNMENT.md            # Feladatleírás
```

---

## Komponensek

### `agent.py` - Mini-Agent Logika

**MeetingAssistantAgent** osztály:
- `parse_input(user_input)` - Felismeri a user parancsát
  - "weather Budapest" → `{"action": "weather", "params": {"location": "Budapest"}}`
  - "timezone Paris" → `{"action": "timezone", "params": {"location": "Paris"}}`
- `validate_action(parsed)` - Ellenőrzi, hogy minden paraméter megvan-e

**Kulcsszavak:**
- `weather` / `időjárás` → Weather API
- `timezone` / `óra` / `tz` → Timezone API
- `country` / `ország` → Country API
- `location` / `hely` → Geocode API

### `api_clients.py` - API Kliens Wrapper-ek

Minden API-hoz egy osztály:

#### `WeatherClient` - OpenWeatherMap API
```python
client = WeatherClient(api_key="your_key")
result = client.get_weather("Budapest")
# {"success": True, "data": {"temp": 12, "humidity": 65, ...}}
```

#### `TimezoneClient` - WorldTimeAPI
```python
client = TimezoneClient()
result = client.get_timezone_by_city("Paris")
# {"success": True, "data": {"timezone": "Europe/Paris", ...}}
```

#### `CountryClient` - REST Countries API
```python
client = CountryClient()
result = client.get_country_info("Hungary")
# {"success": True, "data": {"capital": "Budapest", "population": ...}}
```

#### `GeocodeClient` - Nominatim (OpenStreetMap)
```python
client = GeocodeClient()
result = client.get_coordinates("Budapest")
# {"success": True, "data": {"latitude": 47.497..., "longitude": 19.040...}}
```

### `formatters.py` - Output Formázás

Szép, emberi szöveget generál:
```python
format_weather(api_response)      # 🌤️ Budapest: 12°C, 65% páratartalom
format_timezone(api_response)     # 🕐 Europe/Budapest (UTC+1)
format_country(api_response)      # 🇭🇺 Hungary - Főváros: Budapest
format_coordinates(api_response)  # 📍 Budapest (47.4979°, 19.0402°)
```

### `main.py` - Fő Orchestration

**MeetingAssistant** osztály:
1. `process_input(user_input)` - Végigmegy parse → validate → execute
2. `execute_action(parsed_input)` - Meghívja a megfelelő API-t
3. `run()` - Interaktív hurok

**Munkafolyamat:**
```
User Input
   ↓
[agent.parse_input()]
   ↓
[agent.validate_action()]
   ↓
[API hívás] (weather_client.get_weather() stb.)
   ↓
[formatters.format_*()]
   ↓
Szép Kimenet
```

---

## Publikus API-k

| Név | URL | Auth | Rate Limit |
|-----|-----|------|-----------|
| **OpenWeatherMap** | `api.openweathermap.org` | API key | 1000/nap (free) |
| **WorldTimeAPI** | `worldtimeapi.org` | Nincs | ~ korlátlan |
| **REST Countries** | `restcountries.com` | Nincs | ~ korlátlan |
| **Nominatim (OSM)** | `nominatim.openstreetmap.org` | User-Agent | 1 req/sec |

---

## Futtatási Példák

### Example 1: Időjárás

```bash
🤖 > weather Budapest

🌤️  Budapest, HU időjárása
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Hőmérséklet: 12°C (érzi: 10°C)
💨 Szél: 3.5 m/s
💧 Páratartalom: 65%
📝 Leírás: Felhős
```

### Example 2: Időzóna

```bash
🤖 > timezone Paris

🕐 Időzóna Információ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 Terület: Europe/Paris
🔔 UTC eltolás: +01:00
⏰ Aktuális idő: 2025-12-23T15:30:45
```

### Example 3: Ország

```bash
🤖 > country Hungary

🇭🇺 Hungary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏛️  Főváros: Budapest
🌍 Régió: Europe
👥 Lakosság: 9 700 000
```

### Example 4: Koordináták

```bash
🤖 > location Budapest

📍 Hely Adatai
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗺️  Név: Budapest, Magyarország
🧭 Koordináták:
   • Szélesség: 47.4979°
   • Hosszúság: 19.0402°
```

---

## Hibakezelés

```python
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()  # HTTP hiba-kezelés
except requests.ConnectionError:
    print("Nincs internetkapcsolat")
except requests.Timeout:
    print("API időkorlát túllépve (5s)")
except requests.HTTPError as e:
    print(f"HTTP hiba: {e.response.status_code}")
```

**Implementálva:**
- ✅ Timeout: 5 másodperc
- ✅ Exception handling: RequestException lekezelés
- ✅ User-friendly error üzenetek
- ✅ "Nincs találat" kezelés

---

## Bővítési Ötletek (Bonus)

1. **Caching** - lekérdezések gyorsítása:
   ```python
   @cache(ttl=300)  # 5 perc cache
   def get_weather(city):
       ...
   ```

2. **Unit tesztek** - pytest-tel:
   ```bash
   pytest tests/test_agent.py
   ```

3. **Konfig file** - YAML-ből:
   ```python
   import yaml
   config = yaml.load(open("config.yml"))
   ```

4. **Multi-language** - i18n szupport:
   ```python
   from gettext import translation
   ```

5. **Webhook** - Slack/Discord integrációhoz:
   ```python
   requests.post(SLACK_WEBHOOK, json={"text": result})
   ```

---

## Tanulási Pontok

### `requests` Library
- GET kérések: `requests.get(url, params={}, timeout=5)`
- JSON parse: `response.json()`
- Error handling: `response.raise_for_status()`
- Headers: `headers={"User-Agent": "..."}`

### API Integration Minta
1. **Dokumentáció olvasása** - endpoint, paraméterek
2. **Auth setup** - API key, username stb.
3. **Request konstruálása** - URL, params, headers
4. **Response parse** - JSON structure megértése
5. **Error handling** - timeout, 404, rate limit
6. **Output format** - felhasználó-barát szöveg

### Mini-Agent Pattern
```
Input → Tokenize/Parse → Recognize Intent → Execute → Format Output
```

---

## Tesztelés

### Manuális

```bash
# 1. Telepítés
pip install -r requirements.txt

# 2. Futtatás
python src/main.py

# 3. Tesztelés (bemenet)
weather Budapest
timezone New York
country France
location Colosseum

# 4. Kilépés
exit
```

### Environment Variable Beállítása (OpenWeatherMap)

```bash
# Windows PowerShell
$env:OPENWEATHER_API_KEY = "your_key_here"
python src/main.py

# Linux/Mac
export OPENWEATHER_API_KEY="your_key_here"
python src/main.py
```

---

## Licenc & Notes

- Ingyenes API-k nyilvános adatokkal
- Educational purpose
- Copyleft-friendly integrációk (OpenStreetMap stb.)

**Házi Feladat Teljesítés:**
- ✅ Publikus API meghívás (4 API)
- ✅ User input feldolgozás
- ✅ Szép output formázás
- ✅ Mini-agent döntéslogika

---

## AI Meeting Assistant - Fő Projekt

