import requests
from datetime import datetime

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_city(name: str, count: int = 5) -> list[dict]:
    params = {"name": name, "count": count, "language": "en", "format": "json"}
    r = requests.get(GEOCODE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("results", []) or []


def fetch_forecast(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m",
        "timezone": "auto",
    }
    r = requests.get(FORECAST_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def choose_location(results: list[dict]) -> dict:
    if not results:
        raise ValueError("Nincs találat erre a városnévre.")

    if len(results) == 1:
        return results[0]

    print("\nTalálatok:")
    for i, loc in enumerate(results, 1):
        name = loc.get("name")
        country = loc.get("country")
        admin = loc.get("admin1")
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        extra = f", {admin}" if admin else ""
        print(f"  {i}) {name}{extra}, {country}  (lat={lat}, lon={lon})")

    while True:
        s = input(f"Válassz 1-{len(results)} (Enter = 1): ").strip()
        if s == "":
            return results[0]
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(results):
                return results[idx - 1]
        print("Érvénytelen választás, próbáld újra.")


def main():
    city = input("Város neve: ").strip()
    if not city:
        print("Üres bemenet.")
        return

    results = geocode_city(city)
    loc = choose_location(results)

    lat = loc["latitude"]
    lon = loc["longitude"]

    data = fetch_forecast(lat, lon)

    place = f"{loc.get('name')}, {loc.get('country')}"
    if loc.get("admin1"):
        place = f"{loc.get('name')}, {loc.get('admin1')}, {loc.get('country')}"

    print("\n--- Időjárás ---")
    print(f"Hely: {place} (lat={lat}, lon={lon})")

    current = data.get("current_weather", {})
    if current:
        temp = current.get("temperature")
        wind = current.get("windspeed")
        wdir = current.get("winddirection")
        ctime = current.get("time")
        print(f"Aktuális: {temp}°C, szél {wind} km/h, irány {wdir}°, idő: {ctime}")
    else:
        print("Nincs current_weather adat.")

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])

    if times and temps:
        print("\nKövetkező 24 óra (órás hőmérséklet):")
        now = datetime.fromisoformat(data["current_weather"]["time"]) if current.get("time") else None

        printed = 0
        for t, temp in zip(times, temps):
            dt = datetime.fromisoformat(t)
            if now and dt < now:
                continue
            print(f"  {t}: {temp}°C")
            printed += 1
            if printed >= 24:
                break
    else:
        print("Nincs hourly adat.")

if __name__ == "__main__":
    main()