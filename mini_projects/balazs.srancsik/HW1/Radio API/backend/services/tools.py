"""
Service layer - LangGraph agent tools implementation.
Following SOLID: Single Responsibility - each tool wrapper has one clear purpose.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
import logging

from domain.interfaces import (
    IWeatherClient, IGeocodeClient, IIPGeolocationClient,
    IFXRatesClient, ICryptoPriceClient, IConversationRepository,
    IRadioBrowserClient
)

logger = logging.getLogger(__name__)


class WeatherTool:
    """Weather forecast tool."""
    
    def __init__(self, client: IWeatherClient):
        self.client = client
        self.name = "weather"
        self.description = "Get weather forecast for a city or coordinates. Useful when user asks about weather, temperature, or forecast."
    
    async def execute(self, city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Get weather forecast."""
        logger.info(f"Weather tool called: city={city}, lat={lat}, lon={lon}")
        result = await self.client.get_forecast(city=city, lat=lat, lon=lon)
        
        if "error" not in result:
            # Format result for agent with today and tomorrow summary
            current_temp = result.get("current_temperature", "N/A")
            hourly = result.get("hourly_forecast", {})
            
            # Extract tomorrow's data (hours 24-47 in the forecast)
            tomorrow_temps = hourly.get("temperature_2m", [])[24:48] if len(hourly.get("temperature_2m", [])) > 24 else []
            tomorrow_avg = sum(tomorrow_temps) / len(tomorrow_temps) if tomorrow_temps else None
            tomorrow_min = min(tomorrow_temps) if tomorrow_temps else None
            tomorrow_max = max(tomorrow_temps) if tomorrow_temps else None
            
            # Format summary
            summary = f"Current temperature: {current_temp}°C. "
            if tomorrow_avg:
                summary += f"Tomorrow's forecast: Min {tomorrow_min:.1f}°C, Max {tomorrow_max:.1f}°C, Avg {tomorrow_avg:.1f}°C."
            
            return {
                "success": True,
                "message": summary,
                "data": {
                    **result,
                    "tomorrow": {
                        "min_temp": tomorrow_min,
                        "max_temp": tomorrow_max,
                        "avg_temp": tomorrow_avg
                    } if tomorrow_avg else None
                },
                "system_message": f"Fetched weather forecast for location ({result['location']['latitude']}, {result['location']['longitude']}). {summary}"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "system_message": f"Failed to fetch weather: {result['error']}"
            }


class GeocodeTool:
    """Geocoding and reverse geocoding tool."""
    
    def __init__(self, client: IGeocodeClient):
        self.client = client
        self.name = "geocode"
        self.description = "Convert address to coordinates or coordinates to address. Useful for location lookups."
    
    async def execute(self, address: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Geocode or reverse geocode."""
        logger.info(f"Geocode tool called: address={address}, lat={lat}, lon={lon}")
        
        if address:
            result = await self.client.geocode(address)
        elif lat is not None and lon is not None:
            result = await self.client.reverse_geocode(lat, lon)
        else:
            return {
                "success": False,
                "error": "Either address or coordinates required",
                "system_message": "Geocoding failed: missing parameters"
            }
        
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "system_message": f"Geocoded location: {result.get('display_name', 'Unknown')}"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "system_message": f"Geocoding failed: {result['error']}"
            }


class IPGeolocationTool:
    """IP geolocation tool."""
    
    def __init__(self, client: IIPGeolocationClient):
        self.client = client
        self.name = "ip_geolocation"
        self.description = "Get geographic location from IP address. Useful when user provides or asks about IP addresses."
    
    async def execute(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP."""
        logger.info(f"IP geolocation tool called: ip={ip_address}")
        result = await self.client.get_location(ip_address)
        
        if "error" not in result:
            location_str = f"{result.get('city', 'Unknown')}, {result.get('country', 'Unknown')}"
            return {
                "success": True,
                "data": result,
                "system_message": f"Resolved IP {ip_address} to {location_str} (lat: {result.get('latitude')}, lon: {result.get('longitude')})"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "system_message": f"IP geolocation failed: {result['error']}"
            }


class FXRatesTool:
    """Foreign exchange rates tool."""
    
    def __init__(self, client: IFXRatesClient):
        self.client = client
        self.name = "fx_rates"
        self.description = "Get foreign exchange rates between currencies. Useful for currency conversion questions."
    
    async def execute(self, base: str, target: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange rate."""
        logger.info(f"FX rates tool called: {base} -> {target}, date={date}")
        result = await self.client.get_rate(base, target, date)
        
        if "error" not in result:
            rate = result.get("rate")
            return {
                "success": True,
                "data": result,
                "system_message": f"1 {base} equals {rate} {target} (as of {result.get('date')})"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "system_message": f"FX rate lookup failed: {result['error']}"
            }


class CryptoPriceTool:
    """Cryptocurrency price tool."""
    
    def __init__(self, client: ICryptoPriceClient):
        self.client = client
        self.name = "crypto_price"
        self.description = "Get current cryptocurrency prices. Useful when user asks about Bitcoin, Ethereum, or other crypto prices."
    
    async def execute(self, symbol: str, fiat: str = "USD") -> Dict[str, Any]:
        """Get crypto price."""
        logger.info(f"Crypto price tool called: {symbol} in {fiat}")
        result = await self.client.get_price(symbol, fiat)
        
        if "error" not in result:
            price = result.get("price")
            change = result.get("change_24h", 0)
            return {
                "success": True,
                "data": result,
                "system_message": f"{symbol} price is {price} {fiat} with a 24h change of {change:+.2f}%"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "system_message": f"Crypto price lookup failed: {result['error']}"
            }


class FileCreationTool:
    """File creation tool for saving user notes/documents."""
    
    def __init__(self, data_dir: str = "data/files"):
        self.data_dir = Path(data_dir)
        self.name = "create_file"
        self.description = "Save text content to a file. Useful when user wants to save notes, plans, or documents."
    
    async def execute(self, user_id: str, filename: str, content: str) -> Dict[str, Any]:
        """Create a file."""
        logger.info(f"File creation tool called: user={user_id}, filename={filename}")
        
        try:
            user_dir = self.data_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = user_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "data": {"path": str(file_path), "size": len(content)},
                "system_message": f"Saved content to {file_path}"
            }
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "system_message": f"Failed to create file: {e}"
            }


class HistorySearchTool:
    """History search tool for searching past conversations."""
    
    def __init__(self, repository: IConversationRepository):
        self.repository = repository
        self.name = "search_history"
        self.description = "Search through past conversation history. Useful when user asks to remember or find previous discussions."
    
    async def execute(self, query: str) -> Dict[str, Any]:
        """Search conversation history."""
        logger.info(f"History search tool called: query='{query}'")
        
        try:
            results = await self.repository.search_messages(query)
            
            # Format results
            formatted_results = [
                {
                    "session": r.session_id,
                    "snippet": r.snippet,
                    "timestamp": r.timestamp.isoformat(),
                    "role": r.role
                }
                for r in results[:10]  # Limit to 10 results
            ]
            
            return {
                "success": True,
                "data": {"results": formatted_results, "count": len(results)},
                "system_message": f"Found {len(results)} messages matching '{query}'"
            }
        except Exception as e:
            logger.error(f"History search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "system_message": f"History search failed: {e}"
            }


class RadioTool:
    """
    Radio browser tool for finding and exploring radio stations worldwide.
    
    Uses the Radio Browser API (https://fi1.api.radio-browser.info) to:
    - Search stations by name, country, language, or genre/tag
    - Get top stations by votes, clicks, or recent activity
    - Browse available countries, languages, and tags
    """
    
    def __init__(self, client: IRadioBrowserClient):
        self.client = client
        self.name = "radio"
        self.description = """Search and explore radio stations worldwide. Supports multiple actions:
- Search by country (country_code like 'HU', 'US', 'GB'), name, language, or tag/genre
- Get top stations globally by votes, clicks, or recent activity
- List available countries, languages, or tags/genres
Useful when user asks about radio stations, music genres, or wants to discover new stations."""
    
    async def execute(
        self,
        action: str = "search",
        country_code: Optional[str] = None,
        country: Optional[str] = None,
        name: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        by: str = "votes",
        limit: int = 10,
        filter_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute radio browser actions.
        
        Args:
            action: One of 'search', 'top', 'countries', 'languages', 'tags'
            country_code: ISO country code for search (e.g., 'HU', 'US')
            country: Country name for search
            name: Station name to search for
            language: Language to filter by
            tag: Genre/tag to filter by
            by: For 'top' action - 'votes', 'clicks', 'recent_clicks', 'recently_changed'
            limit: Maximum number of results
            filter_tag: For 'tags' action - filter tags by name
        """
        logger.info(f"Radio tool called: action={action}, country_code={country_code}, name={name}, tag={tag}, limit={limit}")
        
        try:
            if action == "search":
                result = await self.client.search_stations(
                    name=name,
                    country=country,
                    country_code=country_code,
                    language=language,
                    tag=tag,
                    order=by,
                    limit=limit
                )
            elif action == "top":
                result = await self.client.get_top_stations(by=by, limit=limit)
            elif action == "countries":
                result = await self.client.get_countries()
            elif action == "languages":
                result = await self.client.get_languages()
            elif action == "tags":
                result = await self.client.get_tags(filter_tag=filter_tag)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "system_message": f"Unknown radio action: {action}. Use: search, top, countries, languages, tags"
                }
            
            logger.info(f"Radio tool result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            
            if "error" in result:
                logger.error(f"Radio tool error: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "system_message": f"Radio API error: {result['error']}"
                }
            
            # Format response based on action type
            if action in ("search", "top"):
                return self._format_stations_response(result, action)
            elif action == "countries":
                return self._format_countries_response(result)
            elif action == "languages":
                return self._format_languages_response(result)
            elif action == "tags":
                return self._format_tags_response(result)
            
        except Exception as e:
            logger.error(f"Radio tool exception: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "system_message": f"Radio tool failed: {e}"
            }
    
    def _format_stations_response(self, result: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Format stations search/top response."""
        stations = result.get("stations", [])
        
        if not stations:
            filters = result.get("filters", {})
            filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items() if v) if filters else "none"
            return {
                "success": False,
                "error": f"No radio stations found with filters: {filter_desc}",
                "system_message": f"No stations found matching criteria"
            }
        
        # Build summary
        if action == "top":
            ranked_by = result.get("ranked_by", "votes")
            summary = f"Top {len(stations)} radio stations by {ranked_by}:\n\n"
        else:
            summary = f"Found {len(stations)} radio stations:\n\n"
        
        for idx, station in enumerate(stations, 1):
            summary += f"{idx}. 📻 **{station['name']}**\n"
            if station.get('country'):
                summary += f"   🌍 {station['country']}"
                if station.get('language'):
                    summary += f" | 🗣️ {station['language']}"
                summary += "\n"
            if station.get('tags'):
                summary += f"   🏷️ {station['tags']}\n"
            if station.get('quality'):
                summary += f"   🎧 {station['quality']}\n"
            if station.get('votes') or station.get('click_count'):
                summary += f"   ⭐ {station.get('votes', 0)} votes | 👆 {station.get('click_count', 0)} clicks\n"
            if station.get('stream_url'):
                summary += f"   🔗 {station['stream_url']}\n"
            summary += "\n"
        
        return {
            "success": True,
            "message": summary,
            "data": result,
            "system_message": f"Retrieved {len(stations)} radio stations"
        }
    
    def _format_countries_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format countries list response."""
        countries = result.get("countries", [])
        total = result.get("total_countries", len(countries))
        
        summary = f"Top {len(countries)} countries with radio stations (of {total} total):\n\n"
        for c in countries[:20]:
            summary += f"• **{c['name']}** ({c['code']}): {c['station_count']} stations\n"
        
        if len(countries) > 20:
            summary += f"\n... and {len(countries) - 20} more countries"
        
        return {
            "success": True,
            "message": summary,
            "data": result,
            "system_message": f"Retrieved {len(countries)} countries with radio stations"
        }
    
    def _format_languages_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format languages list response."""
        languages = result.get("languages", [])
        total = result.get("total_languages", len(languages))
        
        summary = f"Top {len(languages)} languages with radio stations (of {total} total):\n\n"
        for lang in languages[:20]:
            summary += f"• **{lang['name']}**: {lang['station_count']} stations\n"
        
        if len(languages) > 20:
            summary += f"\n... and {len(languages) - 20} more languages"
        
        return {
            "success": True,
            "message": summary,
            "data": result,
            "system_message": f"Retrieved {len(languages)} languages with radio stations"
        }
    
    def _format_tags_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tags/genres list response."""
        tags = result.get("tags", [])
        total = result.get("total_tags", len(tags))
        filter_used = result.get("filter")
        
        if filter_used:
            summary = f"Tags matching '{filter_used}' ({len(tags)} found):\n\n"
        else:
            summary = f"Top {len(tags)} radio genres/tags (of {total} total):\n\n"
        
        for t in tags[:30]:
            summary += f"• **{t['name']}**: {t['station_count']} stations\n"
        
        if len(tags) > 30:
            summary += f"\n... and {len(tags) - 30} more tags"
        
        return {
            "success": True,
            "message": summary,
            "data": result,
            "system_message": f"Retrieved {len(tags)} radio tags/genres"
        }
