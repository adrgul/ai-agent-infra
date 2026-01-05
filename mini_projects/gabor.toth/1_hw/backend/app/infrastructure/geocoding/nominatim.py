from ...domain.models import Coordinates
from ...domain.ports import GeocodingPort
from ..http.client import AsyncHttpClient
from ...config.settings import settings


class NominatimGeocoder(GeocodingPort):
    def __init__(self):
        self.base_url = settings.nominatim_url

    async def get_coordinates(self, city: str) -> Coordinates:
        async with AsyncHttpClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={"q": city, "format": "json", "limit": 1},
                headers={"User-Agent": "CityBriefing/1.0"}
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError(f"City '{city}' not found")
            result = data[0]
            return Coordinates(lat=float(result["lat"]), lon=float(result["lon"]))
