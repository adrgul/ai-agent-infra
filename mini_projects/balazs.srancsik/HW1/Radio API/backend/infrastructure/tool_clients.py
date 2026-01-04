"""
Infrastructure layer - External API client implementations.
Following SOLID: Single Responsibility - each client handles one external service.
Open/Closed Principle - easy to add new tool clients without modifying existing ones.
"""
import httpx
from typing import Dict, Any, Optional
from domain.interfaces import (
    IWeatherClient, IGeocodeClient, IIPGeolocationClient, 
    IFXRatesClient, ICryptoPriceClient, IRadioBrowserClient
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


class RadioBrowserClient(IRadioBrowserClient):
    """
    Radio Browser API client using direct HTTP calls to Radio Browser API servers.
    
    API Documentation: https://api.radio-browser.info
    
    Supports:
    - Advanced station search (by name, country, language, tag, etc.)
    - Top stations by votes, clicks, or recent activity
    - Browse available countries, languages, and tags/genres
    """
    
    API_SERVERS = [
        "https://de1.api.radio-browser.info",
        "https://fi1.api.radio-browser.info",
        "https://nl1.api.radio-browser.info",
        "https://at1.api.radio-browser.info",
    ]
    USER_AGENT = "AI-Agent-RadioBrowser/1.0"
    
    def __init__(self):
        self._working_server: Optional[str] = None
    
    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async HTTP request to the Radio Browser API with server fallback."""
        
        servers_to_try = [self._working_server] if self._working_server else []
        servers_to_try.extend([s for s in self.API_SERVERS if s != self._working_server])
        
        last_error = None
        
        for server in servers_to_try:
            if not server:
                continue
            url = f"{server}{endpoint}"
            logger.info(f"Radio Browser API request: {url} params={params}")
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.get(
                        url,
                        params=params,
                        headers={"User-Agent": self.USER_AGENT}
                    )
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"Radio Browser API response from {server}: status={response.status_code}, type={type(data).__name__}, len={len(data) if isinstance(data, list) else 'N/A'}")
                    self._working_server = server
                    return data
            except httpx.HTTPStatusError as e:
                logger.error(f"Radio Browser API HTTP error from {server}: {e}")
                last_error = f"API request failed: {e.response.status_code}"
            except httpx.ConnectError as e:
                logger.warning(f"Radio Browser API connection error from {server}: {e}")
                last_error = f"Connection failed: {str(e)}"
            except httpx.TimeoutException as e:
                logger.warning(f"Radio Browser API timeout from {server}: {e}")
                last_error = f"Request timed out: {str(e)}"
            except httpx.RequestError as e:
                logger.warning(f"Radio Browser API request error from {server}: {e}")
                last_error = f"Request failed: {str(e)}"
            except Exception as e:
                logger.error(f"Radio Browser API error from {server}: {e}", exc_info=True)
                last_error = str(e)
        
        logger.error(f"All Radio Browser API servers failed. Last error: {last_error}")
        return {"error": f"All API servers failed. Last error: {last_error}"}
    
    def _format_station(self, station: Dict[str, Any]) -> Dict[str, Any]:
        """Format a station response into a clean structure."""
        codec = station.get("codec", "Unknown")
        bitrate = station.get("bitrate", 0)
        quality = f"{codec} @ {bitrate}kbps" if bitrate else codec
        
        return {
            "uuid": station.get("stationuuid"),
            "name": station.get("name", "Unknown Station"),
            "country": station.get("country", ""),
            "country_code": station.get("countrycode", ""),
            "language": station.get("language", ""),
            "tags": station.get("tags", ""),
            "homepage": station.get("homepage") or None,
            "stream_url": station.get("url_resolved") or station.get("url"),
            "favicon": station.get("favicon") or None,
            "quality": quality,
            "votes": station.get("votes", 0),
            "click_count": station.get("clickcount", 0),
            "is_working": station.get("lastcheckok") == 1,
        }
    
    async def search_stations(
        self,
        name: Optional[str] = None,
        country: Optional[str] = None,
        country_code: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        order: str = "votes",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Advanced search for radio stations with multiple filters.
        
        Args:
            name: Station name (partial match)
            country: Country name (partial match)
            country_code: ISO 3166-1 alpha-2 country code (exact match)
            language: Language name (partial match)
            tag: Tag/genre (partial match)
            order: Sort order - votes, clickcount, name, country, language, etc.
            limit: Maximum number of results (default 10)
        
        Returns:
            Dict with stations list and count
        """
        params = {
            "order": order,
            "reverse": "true",
            "limit": limit,
            "hidebroken": "true",
        }
        
        if name:
            params["name"] = name
        if country:
            params["country"] = country
        if country_code:
            params["countrycode"] = country_code.upper()
        if language:
            params["language"] = language
        if tag:
            params["tag"] = tag
        
        logger.info(f"Searching radio stations with params: {params}")
        data = await self._request("/json/stations/search", params)
        
        if isinstance(data, dict) and "error" in data:
            return data
        
        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}
        
        stations = [self._format_station(s) for s in data]
        
        logger.info(f"Found {len(stations)} radio stations")
        return {
            "stations": stations,
            "count": len(stations),
            "filters": {
                "name": name,
                "country": country,
                "country_code": country_code,
                "language": language,
                "tag": tag,
            }
        }
    
    async def get_top_stations(self, by: str = "votes", limit: int = 10) -> Dict[str, Any]:
        """
        Get top stations by votes, clicks, or recent activity.
        
        Args:
            by: Ranking type - "votes" (topvote), "clicks" (topclick), 
                "recent_clicks" (lastclick), "recently_changed" (lastchange)
            limit: Maximum number of results
        
        Returns:
            Dict with stations list and count
        """
        endpoint_map = {
            "votes": "/json/stations/topvote",
            "clicks": "/json/stations/topclick",
            "recent_clicks": "/json/stations/lastclick",
            "recently_changed": "/json/stations/lastchange",
        }
        
        endpoint = endpoint_map.get(by, "/json/stations/topvote")
        endpoint = f"{endpoint}/{limit}"
        
        logger.info(f"Fetching top stations by {by}, limit {limit}")
        data = await self._request(endpoint)
        
        if isinstance(data, dict) and "error" in data:
            return data
        
        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}
        
        stations = [self._format_station(s) for s in data]
        
        logger.info(f"Retrieved {len(stations)} top stations by {by}")
        return {
            "stations": stations,
            "count": len(stations),
            "ranked_by": by
        }
    
    async def get_countries(self) -> Dict[str, Any]:
        """
        Get list of available countries with station counts.
        
        Returns:
            Dict with countries list
        """
        logger.info("Fetching available countries")
        data = await self._request("/json/countries")
        
        if isinstance(data, dict) and "error" in data:
            return data
        
        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}
        
        countries = [
            {
                "name": c.get("name", ""),
                "code": c.get("iso_3166_1", ""),
                "station_count": c.get("stationcount", 0)
            }
            for c in data
            if c.get("stationcount", 0) > 0
        ]
        
        countries.sort(key=lambda x: x["station_count"], reverse=True)
        
        logger.info(f"Retrieved {len(countries)} countries")
        return {
            "countries": countries[:50],
            "total_countries": len(countries)
        }
    
    async def get_languages(self) -> Dict[str, Any]:
        """
        Get list of available languages with station counts.
        
        Returns:
            Dict with languages list
        """
        logger.info("Fetching available languages")
        data = await self._request("/json/languages")
        
        if isinstance(data, dict) and "error" in data:
            return data
        
        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}
        
        languages = [
            {
                "name": lang.get("name", ""),
                "iso_639": lang.get("iso_639"),
                "station_count": lang.get("stationcount", 0)
            }
            for lang in data
            if lang.get("stationcount", 0) > 0
        ]
        
        languages.sort(key=lambda x: x["station_count"], reverse=True)
        
        logger.info(f"Retrieved {len(languages)} languages")
        return {
            "languages": languages[:50],
            "total_languages": len(languages)
        }
    
    async def get_tags(self, filter_tag: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of available tags/genres with station counts.
        
        Args:
            filter_tag: Optional filter to search for specific tags
        
        Returns:
            Dict with tags list
        """
        endpoint = f"/json/tags/{filter_tag}" if filter_tag else "/json/tags"
        
        logger.info(f"Fetching tags{f' matching {filter_tag}' if filter_tag else ''}")
        data = await self._request(endpoint)
        
        if isinstance(data, dict) and "error" in data:
            return data
        
        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}
        
        tags = [
            {
                "name": t.get("name", ""),
                "station_count": t.get("stationcount", 0)
            }
            for t in data
            if t.get("stationcount", 0) > 0
        ]
        
        tags.sort(key=lambda x: x["station_count"], reverse=True)
        
        logger.info(f"Retrieved {len(tags)} tags")
        return {
            "tags": tags[:100],
            "total_tags": len(tags),
            "filter": filter_tag
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute a radio browser action based on provided parameters.
        
        Supported actions:
        - search: Search stations with filters (name, country, country_code, language, tag)
        - top: Get top stations (by: votes, clicks, recent_clicks, recently_changed)
        - countries: List available countries
        - languages: List available languages
        - tags: List available tags/genres
        """
        action = kwargs.get("action", "search")
        
        if action == "search":
            return await self.search_stations(
                name=kwargs.get("name"),
                country=kwargs.get("country"),
                country_code=kwargs.get("country_code"),
                language=kwargs.get("language"),
                tag=kwargs.get("tag"),
                order=kwargs.get("order", "votes"),
                limit=kwargs.get("limit", 10)
            )
        elif action == "top":
            return await self.get_top_stations(
                by=kwargs.get("by", "votes"),
                limit=kwargs.get("limit", 10)
            )
        elif action == "countries":
            return await self.get_countries()
        elif action == "languages":
            return await self.get_languages()
        elif action == "tags":
            return await self.get_tags(kwargs.get("filter_tag"))
        else:
            return {"error": f"Unknown action: {action}. Supported: search, top, countries, languages, tags"}
