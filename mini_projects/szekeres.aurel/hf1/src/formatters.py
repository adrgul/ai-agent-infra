"""
Output formatters - Szép, emberi szöveget generálunk
"""
from typing import Dict, Any


def format_weather(api_response: Dict[str, Any]) -> str:
    """
    Szép időjárás info kiíratása.

    Args:
        api_response: WeatherClient visszatérési értéke

    Returns:
        str: Formázott szöveg
    """
    if not api_response.get("success"):
        return f"❌ Hiba: {api_response.get('error', 'Ismeretlen hiba')}"

    data = api_response["data"]
    return f"""
🌤️  {data['city']}, {data['country']} időjárása
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Hőmérséklet: {data['temp']}°C (érzi: {data['feels_like']}°C)
💨 Szél: {data['wind_speed']} m/s
💧 Páratartalom: {data['humidity']}%
📝 Leírás: {data['description'].capitalize()}
""".strip()


def format_timezone(api_response: Dict[str, Any]) -> str:
    """
    Szép timezone info kiíratása.

    Args:
        api_response: TimezoneClient visszatérési értéke

    Returns:
        str: Formázott szöveg
    """
    if not api_response.get("success"):
        return f"❌ Hiba: {api_response.get('error', 'Ismeretlen hiba')}"

    data = api_response["data"]
    return f"""
🕐 Időzóna Információ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 Terület: {data['timezone']}
🔔 UTC eltolás: {data['utc_offset']}
⏰ Aktuális idő: {data['current_time'][:19]}
""".strip()


def format_country(api_response: Dict[str, Any]) -> str:
    """
    Szép ország info kiíratása.

    Args:
        api_response: CountryClient visszatérési értéke

    Returns:
        str: Formázott szöveg
    """
    if not api_response.get("success"):
        return f"❌ Hiba: {api_response.get('error', 'Ismeretlen hiba')}"

    data = api_response["data"]
    population_str = (
        f"{data['population']:,}".replace(",", " ")
        if isinstance(data["population"], int)
        else str(data["population"])
    )

    return f"""
{data['flag']} {data['name']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏛️  Főváros: {data['capital']}
🌍 Régió: {data['region']}
👥 Lakosság: {population_str}
""".strip()


def format_coordinates(api_response: Dict[str, Any]) -> str:
    """
    Szép koordináta info kiíratása.

    Args:
        api_response: GeocodeClient visszatérési értéke

    Returns:
        str: Formázott szöveg
    """
    if not api_response.get("success"):
        return f"❌ Hiba: {api_response.get('error', 'Ismeretlen hiba')}"

    data = api_response["data"]
    return f"""
📍 Hely Adatai
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗺️  Név: {data['name']}
🧭 Koordináták:
   • Szélesség: {data['latitude']:.4f}°
   • Hosszúság: {data['longitude']:.4f}°
""".strip()


def format_error(error_msg: str) -> str:
    """Általános hiba kiíratása."""
    return f"❌ {error_msg}"


def format_my_location(api_response: Dict[str, Any]) -> str:
    """
    Szép geolocation info kiíratása (IP alapján).

    Args:
        api_response: IPGeolocationClient visszatérési értéke

    Returns:
        str: Formázott szöveg
    """
    if not api_response.get("success"):
        return f"❌ Hiba: {api_response.get('error', 'Ismeretlen hiba')}"

    data = api_response["data"]
    return f"""
🌐 Az Ön Helye (IP alapján)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Város: {data['city']}, {data['region']}
🌍 Ország: {data['country']}
🧭 Koordináták: {data['latitude']:.4f}°, {data['longitude']:.4f}°
🕐 Időzóna: {data['timezone']}
🔗 ISP: {data['isp']}
""".strip()
