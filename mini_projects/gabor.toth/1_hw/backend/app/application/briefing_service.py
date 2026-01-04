from datetime import datetime
from ..domain.models import (
    Coordinates, CityBriefingResponse, Activity, Briefing
)
from ..domain.ports import (
    GeocodingPort, PlacesPort, KnowledgePort, LLMPort, HistoryPort
)


class BriefingService:
    def __init__(
        self,
        geocoding: GeocodingPort,
        places: PlacesPort,
        knowledge: KnowledgePort,
        llm: LLMPort,
        history: HistoryPort,
    ):
        self.geocoding = geocoding
        self.places = places
        self.knowledge = knowledge
        self.llm = llm
        self.history = history

    async def generate_briefing(
        self,
        city: str,
        activity: str = None,
    ) -> CityBriefingResponse:
        """Generate a complete city briefing."""
        
        print(f"\n📍 [Service] Starting briefing for: {city}")
        
        # Get city coordinates
        print(f"  1️⃣ Getting coordinates for {city}...")
        coordinates = await self.geocoding.get_coordinates(city)
        print(f"     ✓ Coordinates: {coordinates.lat}, {coordinates.lon}")
        
        # Get city facts
        print(f"  2️⃣ Fetching city facts...")
        facts = await self.knowledge.get_city_facts(city, activity=activity, limit=3)
        print(f"     ✓ Found {len(facts)} facts")
        
        # Prepare context for LLM
        print(f"  3️⃣ Preparing context for AI...")
        context = {
            "activity": activity,
            "city_facts": facts,
        }
        
        # Convert user activity to OpenStreetMap-compatible activity using AI
        original_activity = activity
        if activity:
            print(f"  3️⃣a Converting activity for OpenStreetMap...")
            activity = await self._convert_activity_to_osm(activity)
            if activity != original_activity:
                print(f"     ✓ Converted '{original_activity}' → '{activity}'")
        
        # Generate briefing text
        print(f"  4️⃣ Generating briefing with OpenAI...")
        briefing_text = await self.llm.generate_briefing(city, context)
        print(f"     ✓ Briefing generated")
        
        # Suggested activities based on activity preference
        print(f"  5️⃣ Creating suggested activities...")
        activities = []  # Üres lista - csak koordináták kellenek
        
        # Get nearby places based on activity
        print(f"  6️⃣ Fetching nearby places...")
        nearby_places = []
        
        try:
            # Pass activity and city name to places service for area-based search
            nearby_places = await self.places.get_nearby_places(
                coordinates=coordinates,
                radius_m=2000,  # 2km radius
                limit=5,
                poi_types=None,
                activity=activity,  # Pass activity for Overpass search
                city_name=city  # Pass city name for area-based filtering
            )
            print(f"     ✓ Found {len(nearby_places)} places")
        except Exception as e:
            print(f"     ⚠️ Could not fetch places: {e}")
        
        # Fallback: Add example places if none found
        if not nearby_places:
            print(f"     💡 Adding example places for demo...")
            from ..domain.models import POI
            
            # Generate some demo places around the city center
            nearby_places = [
                POI(
                    type="park",
                    name=f"City Park",
                    distance_m=500,
                    walking_minutes=6,
                    lat=coordinates.lat + 0.005,
                    lon=coordinates.lon + 0.005
                ),
                POI(
                    type="cafe",
                    name=f"Central Cafe",
                    distance_m=800,
                    walking_minutes=10,
                    lat=coordinates.lat - 0.003,
                    lon=coordinates.lon + 0.004
                ),
                POI(
                    type="museum",
                    name=f"City Museum",
                    distance_m=1200,
                    walking_minutes=15,
                    lat=coordinates.lat + 0.004,
                    lon=coordinates.lon - 0.003
                ),
                POI(
                    type="viewpoint",
                    name=f"Scenic Viewpoint",
                    distance_m=1500,
                    walking_minutes=18,
                    lat=coordinates.lat - 0.004,
                    lon=coordinates.lon - 0.005
                ),
                POI(
                    type="restaurant",
                    name=f"Local Restaurant",
                    distance_m=600,
                    walking_minutes=7,
                    lat=coordinates.lat + 0.002,
                    lon=coordinates.lon - 0.002
                ),
            ]
        
        # Build response
        response = CityBriefingResponse(
            city=city,
            coordinates=coordinates,
            recommended_activities=activities,
            city_facts=facts,
            briefing=Briefing(paragraph=briefing_text),
            nearby_places=nearby_places,
            fallback_message=self.places.fallback_message,
            metadata={
                "generated_at": datetime.now().isoformat(),
            }
        )
        
        # Reset fallback message for next request
        self.places.fallback_message = None
        
        # Save to history
        await self.history.save_briefing(response.model_dump())
        
        return response
    
    async def _convert_activity_to_osm(self, user_activity: str) -> str:
        """
        Convert user input to OpenStreetMap key=value format using AI.
        
        5 main OSM categories:
        - leisure: parkok, pályák, szórakozás
        - sport: sportok, edzőtermek
        - tourism: múzeumok, turisztikai helyek
        - amenity: közintézmények, kávézók, éttermek
        - shop: üzletek, bevásárlás
        
        Examples:
        - "úsznék egy jó nagyot" → "sport=swimming"
        - "parkok" → "leisure=park"
        - "múzeum" → "tourism=museum"
        - "kávé" → "amenity=cafe"
        - "bevásárlás" → "shop=supermarket"
        
        Returns format: "key=value" (e.g., "leisure=park")
        """
        from ..infrastructure.http.client import AsyncHttpClient
        from ..config.settings import settings
        
        # If already in key=value format, return as-is
        if "=" in user_activity:
            return user_activity.lower()
        
        prompt = f"""
        A felhasználó ezt szeretné tenni: "{user_activity}"
        
        Az OpenStreetMap 5 fő kategóriája:
        
        1. leisure - szabadidős tevékenységek
           Értékek: park, track, playground, swimming_pool, sports_centre, stadium
           Példák: "parkok", "pályák", "úszómedence"
        
        2. sport - sportok és edzés
           Értékek: swimming, soccer, tennis, gym, martial_arts, running
           Példák: "úszás", "futás", "edzés"
        
        3. tourism - turizmus
           Értékek: museum, viewpoint, artwork, castle, monument, gallery, theatre
           Példák: "múzeum", "kilátó", "kastély"
        
        4. amenity - közintézmények
           Értékek: cafe, restaurant, pub, bar, library, theatre, cinema, parking
           Példák: "kávé", "étterem", "uszoda", "mozi"
        
        5. shop - üzletek
           Értékek: supermarket, mall, clothing, food, books, toys, sports
           Példák: "bevásárlás", "ruhabolt", "élelmiszerbolt"
        
        Értelmezd a felhasználó szándékát és add vissza a megfelelő "kategória=érték" párt!
        
        VÁLASZOLJ CSAK a "key=value" formátumban, semmi más! 
        Pl: "leisure=park" vagy "sport=swimming" vagy "tourism=museum"
        """
        
        try:
            # Call OpenAI to intelligently map the activity
            async with AsyncHttpClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system", 
                                "content": """Te egy OpenStreetMap aktivitás-mapping asszisztens vagy. 
                                A felhasználó szándékát az 5 OSM kategória valamelyikébe és egy konkrét értékre lefordítod.
                                Az eredmény always "key=value" formátum legyen (pl: "leisure=park", "sport=swimming").
                                Gondolkodj logikusan és értelmezd a szándékot, még ha az nem is egyértelmű."""
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 30
                    },
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                converted = data["choices"][0]["message"]["content"].strip().lower()
                
                # Validate the response format (should be key=value)
                if "=" in converted:
                    key, value = converted.split("=", 1)
                    # Validate that key is one of the 5 categories
                    valid_keys = ["leisure", "sport", "tourism", "amenity", "shop"]
                    if key in valid_keys:
                        return f"{key}={value}"
                
                # If validation fails, return original
                print(f"     ⚠️ Invalid AI response: '{converted}', using original")
                return user_activity.lower()
        except Exception as e:
            print(f"     ⚠️ Activity conversion error: {e}")
            return user_activity.lower()
