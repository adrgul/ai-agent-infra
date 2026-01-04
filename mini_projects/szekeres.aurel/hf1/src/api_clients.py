"""
API clients: Publikus API-k meghívása requests-el
"""
import requests
from typing import Dict, Any, Optional


class WeatherClient:
    """OpenWeatherMap API - ingyenes verzió (API key szükséges)"""

    def __init__(self, api_key: str = ""):
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.api_key = api_key

    def get_weather(self, city: str) -> Dict[str, Any]:
        """
        Lekéri az aktuális időjárást egy városhoz.

        Args:
            city: Város neve (pl. "Budapest")

        Returns:
            dict: {"success": bool, "data": {...}, "error": str}
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenWeatherMap API key nincs beállítva. Regisztrálj a https://openweathermap.org/api -en.",
            }

        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "hu",
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "data": {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temp": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                },
            }
        except requests.RequestException as e:
            return {"success": False, "error": f"OpenWeatherMap API hiba: {str(e)}"}


class IPGeolocationClient:
    """IP-based geolocation - ip-api.com fallback-kel"""

    def __init__(self):
        self.base_urls = [
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/json",
        ]

    def get_my_location(self) -> Dict[str, Any]:
        """
        Lekéri az IP-t és közelítő helyinformációt.
        (Egyszerűsített: csak IP + fallback helyadatok)

        Returns:
            dict: {"success": bool, "data": {...}, "error": str}
        """
        try:
            # Próbáljunk lekérni az IP-t
            response = requests.get(self.base_urls[0], timeout=5)
            response.raise_for_status()
            
            data = response.json()
            ip_address = data.get("ip", "N/A")
            
            # Közelítő helyadatok (hardcoded minta)
            # Valós helyzetben ip-api.com vagy maxmind lenne jó
            return {
                "success": True,
                "data": {
                    "ip_address": ip_address,
                    "city": "Budapest",
                    "region": "Budapest",
                    "country": "Hungary",
                    "latitude": 47.4979,
                    "longitude": 19.0402,
                    "timezone": "Europe/Budapest",
                    "isp": "ISP Info",
                },
            }
        except requests.RequestException as e:
            return {"success": False, "error": f"IP Geolocation API hiba: {str(e)}"}


class TimezoneClient:
    """WorldTimeAPI - ingyenes timezone info"""

    def __init__(self):
        self.base_url = "https://worldtimeapi.org/api/timezone"

    def get_timezone_by_city(self, city: str) -> Dict[str, Any]:
        """
        Meghatározza a város időzónáját.
        
        Args:
            city: Város neve

        Returns:
            dict: {"success": bool, "data": {...}, "error": str}
        """
        # Tanúsítani kell: város → timezone mapping
        # Egyszerűbb módszer: összes timezone lekérése és keresés
        try:
            response = requests.get(f"{self.base_url}", timeout=5)
            response.raise_for_status()

            timezones = response.json()

            # Keresünk a város szerint
            matching_tz = None
            for tz in timezones:
                if city.lower() in tz.lower():
                    matching_tz = tz
                    break

            if not matching_tz:
                # Fallback: próbáljuk "Europe/[város]" formában
                matching_tz = f"Europe/{city.capitalize()}"

            # Lekérjük az adatokat erről az időzónáról
            detail_response = requests.get(
                f"{self.base_url}/{matching_tz}", timeout=5
            )
            detail_response.raise_for_status()

            detail_data = detail_response.json()
            return {
                "success": True,
                "data": {
                    "timezone": matching_tz,
                    "utc_offset": detail_data["utc_offset"],
                    "current_time": detail_data["datetime"],
                },
            }
        except requests.RequestException as e:
            return {"success": False, "error": f"Timezone API hiba: {str(e)}"}


class CountryClient:
    """REST Countries API - ingyenes ország info"""

    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"

    def get_country_info(self, country: str) -> Dict[str, Any]:
        """
        Lekéri az ország adatait.

        Args:
            country: Ország neve (pl. "Hungary")

        Returns:
            dict: {"success": bool, "data": {...}, "error": str}
        """
        try:
            response = requests.get(
                f"{self.base_url}/name/{country}",
                timeout=5,
            )
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                country_data = data[0]
                return {
                    "success": True,
                    "data": {
                        "name": country_data["name"]["common"],
                        "capital": country_data.get("capital", ["N/A"])[0],
                        "region": country_data.get("region", "N/A"),
                        "population": country_data.get("population", "N/A"),
                        "flag": country_data.get("flag", "🏳️"),
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"Nem találtam: {country}",
                }

        except requests.RequestException as e:
            return {"success": False, "error": f"REST Countries API hiba: {str(e)}"}


class GeocodeClient:
    """Nominatim (OpenStreetMap) - ingyenes geocoding"""

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"

    def get_coordinates(self, location: str) -> Dict[str, Any]:
        """
        Lekéri a hely koordinátáit (lat/lon).

        Args:
            location: Hely neve (pl. "Budapest")

        Returns:
            dict: {"success": bool, "data": {...}, "error": str}
        """
        try:
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
            }
            response = requests.get(
                self.base_url,
                params=params,
                headers={"User-Agent": "MeetingAI-Agent/1.0"},
                timeout=5,
            )
            response.raise_for_status()

            data = response.json()
            if data:
                place = data[0]
                return {
                    "success": True,
                    "data": {
                        "name": place.get("display_name", location),
                        "latitude": float(place["lat"]),
                        "longitude": float(place["lon"]),
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"Nem találtam helyet: {location}",
                }

        except requests.RequestException as e:
            return {"success": False, "error": f"Nominatim API hiba: {str(e)}"}
