import math
from typing import Optional
from ...domain.models import Coordinates, POI
from ...domain.ports import PlacesPort
from ..http.client import AsyncHttpClient
from ...config.settings import settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate distance in meters between two coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return int(R * c)


# Simple activity to OSM key mapping  
ACTIVITY_MAPPING = {
    # Primary activities
    "parks": ["leisure=park"],
    "parkok": ["leisure=park"],
    "museums": ["tourism=museum"],
    "múzeumok": ["tourism=museum"],
    "cafes": ["amenity=cafe"],
    "kávézók": ["amenity=cafe"],
    "restaurants": ["amenity=restaurant"],
    "etterem": ["amenity=restaurant"],
    "churches": ["amenity=place_of_worship"],
    "templomok": ["amenity=place_of_worship"],
    "nightlife": ["amenity=bar", "amenity=pub"],
    "éjszakai": ["amenity=bar", "amenity=pub"],
    
    # Sports & Activity
    "hiking": ["leisure=park", "tourism=viewpoint"],
    "futás": ["leisure=track", "leisure=park"],
    "sports": ["leisure=sports_centre", "leisure=stadium"],
    "sportok": ["leisure=sports_centre", "leisure=stadium"],
    
    # Sightseeing & Culture
    "viewpoints": ["tourism=viewpoint"],
    "kilátók": ["tourism=viewpoint"],
    "cultural": ["tourism=museum", "amenity=theatre"],
    "kultúra": ["tourism=museum", "amenity=theatre"],
    "entertainment": ["amenity=cinema", "amenity=theatre"],
    "szórakozás": ["amenity=cinema", "amenity=theatre"],
    
    # Shopping
    "shopping": ["shop=supermarket", "shop=mall"],
    "bevásárlás": ["shop=supermarket", "shop=mall"],
    
    # Water & Swimming activities
    "swim": ["leisure=swimming_pool", "natural=water"],
    "swimming": ["leisure=swimming_pool", "natural=water"],
    "water": ["leisure=swimming_pool", "natural=water"],
    "vízpart": ["leisure=swimming_pool", "natural=water"],
    
    # Test fallback
    "test_fallback": ["nonexistent=key"],
}


class OverpassClient(PlacesPort):
    def __init__(self):
        self.base_url = settings.overpass_url
        self.fallback_message: Optional[str] = None

    async def get_nearby_places(
        self, 
        coordinates: Coordinates, 
        radius_m: int = 2000, 
        limit: int = 5, 
        poi_types: Optional[list[str]] = None,
        activity: Optional[str] = None,
        city_name: Optional[str] = None
    ) -> list[POI]:
        """
        Get nearby places from OpenStreetMap using Overpass API.
        If activity is specified as "key=value" format (e.g., "leisure=park"), use it directly.
        Falls back to demo places if Overpass returns no results.
        """
        pois = []
        
        # Determine which OSM keys to search for
        osm_keys = []
        activity_lower = activity.lower() if activity else None
        
        # Check if activity is in "key=value" format (from OpenAI conversion)
        if activity_lower and "=" in activity_lower:
            # Direct format from OpenAI (e.g., "leisure=park" or "sport=swimming")
            osm_keys = [activity_lower]
            print(f"     🗺️  OpenStreetMap lekérdezés: {activity}")
        elif activity_lower and activity_lower in ACTIVITY_MAPPING:
            # Legacy format - look up in mapping
            osm_keys = ACTIVITY_MAPPING[activity_lower]
            print(f"     🗺️  OpenStreetMap lekérdezés: {activity}")
        else:
            # Default to parks and museums
            osm_keys = ["leisure=park", "tourism=museum", "amenity=cafe"]
            if activity:
                print(f"     🗺️  OpenStreetMap általános keresés: {activity}")
        
        # Build bbox from coordinates and radius
        # 1 degree ≈ 111 km, so radius_m / 111000 = degrees
        radius_degrees = radius_m / 111000
        south = coordinates.lat - radius_degrees
        west = coordinates.lon - radius_degrees
        north = coordinates.lat + radius_degrees
        east = coordinates.lon + radius_degrees
        
        # Try each OSM key separately to avoid overloading the API
        for osm_key in osm_keys[:3]:  # Limit to 3 queries per activity
            query = self._build_overpass_query(osm_key, south, west, north, east)
            await self._execute_query(query, coordinates, activity or "general", pois)
            
            # Stop early if we have enough results
            if len(pois) >= limit:
                break
        
        # Sort by distance and limit
        pois.sort(key=lambda x: x.distance_m)
        pois = pois[:limit]
        
        # If no results, use fallback demo places
        if not pois and activity:
            message = f"⚠️  Nem találtam megfelelő helyeket, a tesztelhetőség érdekében teszt helyeket mutatok ({activity})"
            print(f"     {message}")
            self.fallback_message = message
            pois = self._generate_fallback_places(coordinates, activity, limit)
        
        return pois

    def _build_overpass_query(
        self,
        osm_key: str,
        south: float,
        west: float,
        north: float,
        east: float
    ) -> str:
        """Build a simple Overpass query for a single OSM key with optimized settings."""
        key, value = osm_key.split("=", 1)
        # Use maxsize to limit results, faster for busy servers
        query = f'[out:json][timeout:10][maxsize:536870912];nwr["{key}"="{value}"]({south},{west},{north},{east});out center;'
        return query

    async def _execute_query(
        self,
        query: str,
        coordinates: Coordinates,
        poi_type: str,
        pois: list[POI]
    ) -> None:
        """Execute Overpass query with retry logic and add results to pois list."""
        import asyncio
        
        max_retries = 3
        retry_delay = 2  # seconds
        data = None
        
        # Try multiple times if we get 0 results
        for attempt in range(max_retries):
            try:
                print(f"     📡 Sending Overpass query ({len(query)} chars)..." + (f" (attempt {attempt+1}/{max_retries})" if attempt > 0 else ""))
                async with AsyncHttpClient() as client:
                    response = await client.post(
                        self.base_url,
                        data={"data": query},
                        timeout=30  # Increased timeout from 25
                    )
                    response.raise_for_status()
                    data = response.json()
                    result_count = len(data.get('elements', []))
                    print(f"     ✓ Got {result_count} results")
                    
                    # If we got results, break and process
                    if result_count > 0:
                        break
                    
                    # Got 0 results and this is not the last attempt, retry
                    if attempt < max_retries - 1:
                        print(f"     ⏳ No results yet, waiting {retry_delay}s before retry...")
                        await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"     ❌ Query failed: {str(e)[:100]}")
                    return
                print(f"     ⚠️ Query failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
        
        # Process results if we have any
        if not data:
            return
        
        for element in data.get("elements", []):
            try:
                # Get coordinates from node or way center
                lat = element.get("lat") or element.get("center", {}).get("lat")
                lon = element.get("lon") or element.get("center", {}).get("lon")
                
                if lat and lon:
                    distance_m = haversine_distance(coordinates.lat, coordinates.lon, lat, lon)
                    
                    # Skip if already too far
                    if distance_m > 5000:  # 5km limit
                        continue
                    
                    walking_minutes = max(1, distance_m // 80)  # ~80m per minute
                    
                    # Get name from tags
                    tags = element.get("tags", {})
                    # Determine place type from the element's tags
                    place_type = "place"
                    if "tourism" in tags:
                        place_type = tags.get("tourism", "place")
                    elif "leisure" in tags:
                        place_type = tags.get("leisure", "place")
                    elif "amenity" in tags:
                        place_type = tags.get("amenity", "place")
                    
                    name = tags.get("name", f"{place_type.replace('_', ' ').title()} #{element.get('id')}")
                    
                    pois.append(POI(
                        type=place_type,
                        name=name,
                        distance_m=distance_m,
                        walking_minutes=walking_minutes,
                        lat=lat,
                        lon=lon
                    ))
            except Exception as e:
                # Skip this element if there's an error processing it
                continue

    def _generate_fallback_places(
        self,
        coordinates: Coordinates,
        activity: str,
        limit: int
    ) -> list[POI]:
        """Generate realistic demo places based on activity."""
        demo_places = {
            "hiking": [
                ("Mountain Trail", 2500, 30),
                ("Forest Path", 1800, 22),
                ("Scenic Ridge", 3200, 40),
                ("Valley Loop", 1500, 18),
                ("Peak View", 4000, 50),
            ],
            "futás": [
                ("Athletic Track", 1000, 12),
                ("Running Path", 800, 10),
                ("Sports Park", 1500, 18),
                ("Jogging Trail", 1200, 15),
                ("Fitness Park", 900, 11),
            ],
            "museums": [
                ("National Museum", 800, 10),
                ("Art Gallery", 1200, 15),
                ("History Museum", 1500, 18),
                ("Science Center", 2000, 25),
                ("Local Heritage", 1000, 12),
            ],
            "múzeumok": [
                ("Nemzeti Múzeum", 800, 10),
                ("Képtár", 1200, 15),
                ("Történeti Múzeum", 1500, 18),
                ("Tudományi Központ", 2000, 25),
            ],
            "cafes": [
                ("Central Cafe", 400, 5),
                ("Cozy Corner", 600, 7),
                ("Modern Brew", 800, 10),
                ("Garden Coffee", 1200, 15),
                ("Sunset Roastery", 1500, 18),
            ],
            "kávézók": [
                ("Központi Kávézó", 400, 5),
                ("Barista House", 600, 7),
                ("Modern Kávé", 800, 10),
                ("Kert Kávé", 1200, 15),
            ],
            "parks": [
                ("City Park", 500, 6),
                ("Central Garden", 1000, 12),
                ("Green Space", 800, 10),
                ("Recreation Area", 1500, 18),
                ("Nature Reserve", 2000, 25),
            ],
            "parkok": [
                ("Városi Park", 500, 6),
                ("Központi Kert", 1000, 12),
                ("Zöldterület", 800, 10),
                ("Rekreációs Terület", 1500, 18),
            ],
            "restaurants": [
                ("Local Cuisine", 600, 7),
                ("Fine Dining", 1200, 15),
                ("Street Food", 800, 10),
                ("Traditional Kitchen", 1000, 12),
                ("Modern Fusion", 1500, 18),
            ],
        }
        
        activity_lower = activity.lower()
        places = demo_places.get(activity_lower, demo_places.get("parks"))
        
        pois = []
        for i, (name, distance_m, walking_min) in enumerate(places[:limit]):
            offset = 0.01 * (i + 1)
            pois.append(POI(
                type=activity_lower.replace(" ", "_"),
                name=name,
                distance_m=distance_m,
                walking_minutes=walking_min,
                lat=coordinates.lat + offset,
                lon=coordinates.lon + offset,
            ))
        
        return pois
