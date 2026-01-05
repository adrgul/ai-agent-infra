from ...config.settings import settings
from ...domain.ports import LLMPort
from ..http.client import AsyncHttpClient


class OpenAIClient(LLMPort):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = "gpt-4o-mini"  # Using Responses API compatible model

    async def filter_facts_by_activity(self, city: str, activity: str, facts_text: str) -> list[str]:
        """Filter Wikipedia facts to only relevant information for the activity."""
        if not self.api_key or not facts_text or not activity:
            return []
        
        prompt = f"""A felhasználó {activity} szeretne csinálni {city}-ban. Alább a város Wikipédia cikkéből néhány információ:

"{facts_text}"

Kérlek, azonosítsd be és addd vissza azokat az információ-fragmentumokat (1-3 mondatos részleteket), amelyek relevánsak a "{activity}"-hez. 

Formátum: Minden információt külön sorban adj vissza. Csak a legfontosabbakat, amelyek közvetlenül kapcsolódnak az aktivitáshoz.
Ha nincsenek relevans információk, üres listát adj vissza."""

        try:
            async with AsyncHttpClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Te egy turizmus szakértő vagy. Szűrj információkat az aktivitáshoz kapcsolódó relevans részletekre."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 200
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                result = data["choices"][0]["message"]["content"].strip()
                # Split into lines and filter empty ones
                return [line.strip() for line in result.split("\n") if line.strip()]
        except Exception as e:
            print(f"⚠️ Hiba az információ szűrésében: {e}")
            return []

    async def recommend_poi_types(self, city: str, activity: str) -> list[str]:
        """Get LLM to recommend POI types based on desired activity."""
        if not self.api_key:
            return ["park", "cafe", "museum"]  # Default types
        
        prompt = f"""Valaki {activity} szeretne csinálni {city}-ban. Ajánld meg 3-5 típusú helyet (OSM/Overpass adatbázisból), ahol ellátogathatna.

Elérhető POI típusok: park, museum, cafe, viewpoint, drinking_water, restaurant, library, theater, gallery, market

CSAK vesszővel elválasztott típusok listáját add vissza, semmi mást. Például: "park,cafe,museum" """

        try:
            async with AsyncHttpClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Te egy utazási szakértő vagy. Csak vesszővel elválasztott POI típusok nevét válaszold meg."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 50
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                poi_types_str = data["choices"][0]["message"]["content"].strip()
                return [t.strip() for t in poi_types_str.split(",")]
        except Exception as e:
            print(f"⚠️ Hiba a POI típusok ajánlásában: {e}")
            return []

    async def generate_briefing(self, city: str, context: dict) -> str:
        if not self.api_key:
            return f"Napi tájékoztató {city}-ról: Nem lehet tájékoztatót készíteni API kulcs nélkül. Kérjük, állítsd be az OPENAI_API_KEY értéket a .env fájlban"
        
        facts_str = "Nincsenek elérhető információk"
        if context.get("city_facts"):
            facts_list = context["city_facts"]
            facts_str = "\n".join([f"- {f.title}: {f.content}" for f in facts_list])
        
        activity = context.get("activity", "")
        
        # If activity is provided, customize the prompt to highlight activity-relevant facts
        if activity:
            prompt = f"""Készítsd el {city}-ról a személyre szabott napi tájékoztatót az alábbiak alapján:

Város Információk:
{facts_str}

Felhasználó szándékolt aktivitása: {activity}

Kérlek, írj 3-4 mondatos vonzó tájékoztatót, amely:
1. Kiemeli azokat a város információkat, amelyek relevánsak az "{activity}"-hoz
2. Természetes módon kapcsolódik az aktivitáshoz
3. Cselekvésre ösztönöz és pozitív hangvételt használ
4. Személyre szabott és érdekes információkat tartalmaz

Tartsd röviden és lebilincselõen, hogy az olvasó kedvet kapjon felfedezni a várost!"""
        else:
            prompt = f"""Készítsd el {city}-ról a napi tájékoztatót az alábbi információk alapján:

Város Információk:
{facts_str}

Írj 3-4 mondatos vonzó tájékoztatót, amely:
1. Bemutatja a város legfontosabb jellemzõit
2. Érdekes és vonzó információt tartalmaz
3. Cselekvésre ösztönöz és pozitív hangvételt használ
4. Meghívja az olvasót a város felfedezésére

Tartsd röviden és lebilincselõen!"""

        async with AsyncHttpClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Te egy barátságos városvezetõ vagy, aki napi tájékoztatókat készít. Válaszod csak a tájékoztató legyen, semmi mást nem írj."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 300
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Tájékoztató {city}-ról: Nem sikerült ebben a pillanatban elkészíteni. ({str(e)[:50]})"
