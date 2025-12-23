# 1. Házi Feladat: Publikus API Meghívása Pythonból

## Feladat Specifikációja

**Téma:** Meeting Assistant kontextusban publikus API-k meghívása

### Követelmények

✅ **Kötelező elemek:**
1. Publikus API meghívás (`requests` library)
2. User input kérése az alkalmazástól
3. Szép, emberi szöveget kiíratása
4. Meeting Assistant témához illő API-k

✅ **Bonus pont:**
- Mini-agent logika: kulcsszó-alapú API routing

---

## Az Alkalmazás Koncepciója

### "Meeting Context Assistant"

Egy **mini-agent**, amely meeting előtt/után hasznos információkat gyűjt össze:
- **Hely időjárása** → OpenWeatherMap API
- **Időzóna információ** → Timezone API  
- **Nyilvános terek adatai** → OpenStreetMap / Nominatim API
- **Ország információ** → REST Countries API

#### Működés:
```
User: "weather Budapest"
  ↓
[Mini-Agent Döntés] → Kulcsszó: "weather" → OpenWeatherMap API
  ↓
API Hívás & Feldolgozás
  ↓
Szép Kimenet: "🌤️ Budapest időjárása: 12°C, Частично felhős"
```

---

## Ingyenes API-k Listája

| API | URL | Korlát | Auth |
|-----|-----|--------|------|
| **OpenWeatherMap** | `api.openweathermap.org` | 1000 req/nap | API key |
| **GeoNames** | `api.geonames.org` | ingyenes | username |
| **Nominatim (OSM)** | `nominatim.openstreetmap.org` | ingyenes | nincs |
| **REST Countries** | `restcountries.com` | ingyenes | nincs |
| **Timezone API** | `worldtimeapi.org` | ingyenes | nincs |

---

## Felépítés

```
hf1/
├── src/
│   ├── agent.py           # Mini-agent logika (kulcsszó → API)
│   ├── api_clients.py     # API hívások (requests)
│   ├── formatters.py      # Szép output formázás
│   └── main.py            # Entry point
├── requirements.txt       # Python dependencies
└── ASSIGNMENT.md          # Ez a fájl
```

---

## Futtatás

```bash
# 1. Telepítés
pip install -r requirements.txt

# 2. Futtatás
python src/main.py

# 3. Példa interakciók:
# Input:  "weather Budapest"
# Output: 🌤️ Budapest időjárása: 12°C, 65% páratartalom
#
# Input:  "timezone Paris"
# Output: 🕐 Paris időzónája: Europe/Paris (UTC+1)
#
# Input:  "country Hungary"
# Output: 🇭🇺 Magyarország - Főváros: Budapest, 9.7M lakosság
```

---

## Kódstruktúra Outline

### `src/agent.py`
Felismeri a user inputot és dönt, melyik API-t hívja:
```python
def parse_user_input(user_input: str) -> dict:
    # Kulcsszavak: weather, timezone, country, location, etc.
    # Visszatér: {"action": "weather", "params": {"city": "Budapest"}}
```

### `src/api_clients.py`
API hívások (`requests`):
```python
class WeatherClient:
    def get_weather(self, city: str) -> dict:
        # OpenWeatherMap API hívás

class TimezoneClient:
    def get_timezone(self, city: str) -> str:
        # Timezone API hívás
```

### `src/formatters.py`
Szép kimenetek:
```python
def format_weather(data: dict) -> str:
    # "🌤️ Budapest: 12°C, Felhős"
```

### `src/main.py`
User interact, agent döntés, kimenet:
```python
def main():
    while True:
        user_input = input("🤖 Meeting Assistant > ")
        action = parse_user_input(user_input)
        result = execute_action(action)
        print(result)
```

---

## Értékelési Szempontok

| Pont | Feltétel |
|------|----------|
| **10/10** | Legalább 3 API integrálva, mini-agent döntéslogika, szép output |
| **8/10** | 2 API, alapvető agent logika |
| **6/10** | 1 API, user input feldolgozás |
| **+2 bonus** | Hibakezelés, konfigurálható API keys, unit tesztek |

---

## Tippek & Segítség

1. **API Keys**
   - OpenWeatherMap: ingyenes regisztráció (api.openweathermap.org)
   - GeoNames: ingyenes bejelentkezés szükséges
   - Nominatim / REST Countries: nem kell auth

2. **Hibakezelés**
   ```python
   try:
       response = requests.get(url, timeout=5)
       response.raise_for_status()
   except requests.RequestException as e:
       print(f"API hiba: {e}")
   ```

3. **Environment Variables**
   ```bash
   # .env fájl
   OPENWEATHER_API_KEY=your_key_here
   GEONAMES_USERNAME=your_username
   ```

---

## Submit

Elkészült projekt:
```
hf1/
├── src/
│   ├── agent.py
│   ├── api_clients.py
│   ├── formatters.py
│   └── main.py
├── requirements.txt
├── .env.example
├── ASSIGNMENT.md
└── README.md (dokumentáció a te szavaiddal)
```

**GitHub-ra push vagy ZIP-ként beküld.**
