"""
Infrastructure layer - External API client implementations.
Following SOLID: Single Responsibility - each client handles one external service.
Open/Closed Principle - easy to add new tool clients without modifying existing ones.
"""
import httpx
from typing import Dict, Any, Optional
from domain.interfaces import (
    IWeatherClient, IGeocodeClient, IIPGeolocationClient, 
    IFXRatesClient, ICryptoPriceClient
)
import logging

logger = logging.getLogger(__name__)


class OpenMeteoWeatherClient(IWeatherClient):
    """Open-Meteo weather API client."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self, geocode_client: IGeocodeClient):
        self.geocode_client = geocode_client
    
    async def get_forecast(self, city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Get weather forecast."""
        try:
            # If city is provided, geocode it first
            if city and (lat is None or lon is None):
                geo_result = await self.geocode_client.geocode(city)
                if "error" in geo_result:
                    return geo_result
                lat = geo_result["latitude"]
                lon = geo_result["longitude"]
            
            if lat is None or lon is None:
                return {"error": "Either city or coordinates must be provided"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,weathercode",
                        "hourly": "temperature_2m,weathercode",
                        "forecast_days": 2
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Fetched weather for coords ({lat}, {lon})")
                
                return {
                    "location": {"latitude": lat, "longitude": lon},
                    "current_temperature": data["current"]["temperature_2m"],
                    "hourly_forecast": data["hourly"],
                    "units": data.get("hourly_units", {})
                }
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {"error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return await self.get_forecast(**kwargs)


class NominatimGeocodeClient(IGeocodeClient):
    """OpenStreetMap Nominatim geocoding client."""
    
    GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
    REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    
    async def geocode(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.GEOCODE_URL,
                    params={"q": address, "format": "json", "limit": 1},
                    headers={"User-Agent": "AI-Agent-Demo/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    return {"error": f"Location not found: {address}"}
                
                result = data[0]
                logger.info(f"Geocoded '{address}' to ({result['lat']}, {result['lon']})")
                
                return {
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                    "display_name": result["display_name"]
                }
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {"error": str(e)}
    
    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Convert coordinates to address."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.REVERSE_URL,
                    params={"lat": lat, "lon": lon, "format": "json"},
                    headers={"User-Agent": "AI-Agent-Demo/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Reverse geocoded ({lat}, {lon})")
                
                return {
                    "display_name": data["display_name"],
                    "address": data.get("address", {})
                }
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return {"error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        if "address" in kwargs:
            return await self.geocode(kwargs["address"])
        elif "lat" in kwargs and "lon" in kwargs:
            return await self.reverse_geocode(kwargs["lat"], kwargs["lon"])
        return {"error": "Either address or lat/lon required"}


class IPAPIGeolocationClient(IIPGeolocationClient):
    """ipapi.co IP geolocation client."""
    
    BASE_URL = "https://ipapi.co"
    
    async def get_location(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP address."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.BASE_URL}/{ip_address}/json/")
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    return {"error": data["reason"]}
                
                logger.info(f"Resolved IP {ip_address} to {data.get('city')}, {data.get('country_name')}")
                
                return {
                    "ip": ip_address,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude")
                }
        except Exception as e:
            logger.error(f"IP geolocation error: {e}")
            return {"error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return await self.get_location(kwargs.get("ip_address", ""))


class ExchangeRateHostClient(IFXRatesClient):
    """ExchangeRate.host API client - using frankfurter.app (free, no API key needed)."""
    
    BASE_URL = "https://api.frankfurter.app"
    
    async def get_rate(self, base: str, target: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange rate."""
        try:
            # Frankfurter uses date in URL path or 'latest'
            endpoint = f"{self.BASE_URL}/{date if date else 'latest'}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    endpoint,
                    params={"from": base, "to": target}
                )
                response.raise_for_status()
                data = response.json()
                
                # Check if we got a valid response
                if "rates" not in data or target not in data["rates"]:
                    return {"error": f"Exchange rate not available for {base} to {target}"}
                
                rate = data["rates"][target]
                logger.info(f"FX rate: 1 {base} = {rate} {target}")
                
                return {
                    "base": base,
                    "target": target,
                    "rate": rate,
                    "date": data.get("date")
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"FX rate HTTP error: {e}")
            return {"error": f"Currency not supported: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"FX rate error: {e}")
            return {"error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return await self.get_rate(
            kwargs.get("base", "EUR"),
            kwargs.get("target", "USD"),
            kwargs.get("date")
        )


class CoinGeckoCryptoClient(ICryptoPriceClient):
    """CoinGecko cryptocurrency price client."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    async def get_price(self, symbol: str, fiat: str = "USD") -> Dict[str, Any]:
        """Get crypto price."""
        try:
            # Convert symbol to CoinGecko ID (simplified mapping)
            coin_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "USDT": "tether",
                "BNB": "binancecoin",
                "SOL": "solana",
                "ADA": "cardano",
                "XRP": "ripple",
                "DOT": "polkadot"
            }
            coin_id = coin_map.get(symbol.upper(), symbol.lower())
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/simple/price",
                    params={
                        "ids": coin_id,
                        "vs_currencies": fiat.lower(),
                        "include_24hr_change": "true"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if coin_id not in data:
                    return {"error": f"Cryptocurrency {symbol} not found"}
                
                price = data[coin_id][fiat.lower()]
                change_24h = data[coin_id].get(f"{fiat.lower()}_24h_change", 0)
                
                logger.info(f"Crypto price: {symbol} = {price} {fiat}")
                
                return {
                    "symbol": symbol,
                    "fiat": fiat,
                    "price": price,
                    "change_24h": round(change_24h, 2)
                }
        except Exception as e:
            logger.error(f"Crypto price error: {e}")
            return {"error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return await self.get_price(
            kwargs.get("symbol", "BTC"),
            kwargs.get("fiat", "USD")
        )
