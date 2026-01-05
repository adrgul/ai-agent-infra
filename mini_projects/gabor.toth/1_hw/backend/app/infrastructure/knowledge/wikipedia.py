from ...domain.models import CityFact
from ...domain.ports import KnowledgePort
from ..http.client import AsyncHttpClient


class WikipediaClient(KnowledgePort):
    def __init__(self):
        self.base_url = "https://hu.wikipedia.org/w/api.php"

    async def get_city_facts(self, city: str, activity: str = None, limit: int = 3) -> list[CityFact]:
        """Get city facts from Wikipedia API in Hungarian, filtered by activity if provided."""
        facts = []
        full_text = ""
        
        # Wikipedia API requires User-Agent header
        headers = {
            "User-Agent": "VarosBriefing/1.0 (github.com/Global-rd/ai-agents-hu)"
        }
        
        try:
            async with AsyncHttpClient() as client:
                # First, search for the city
                search_response = await client.get(
                    self.base_url,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": city,
                        "srnamespace": "0",
                        "format": "json",
                        "srlimit": "1",
                    },
                    headers=headers
                )
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if not search_data.get("query", {}).get("search"):
                    return facts
                
                # Get the first search result title
                article_title = search_data["query"]["search"][0]["title"]
                
                # Get the article content
                content_response = await client.get(
                    self.base_url,
                    params={
                        "action": "query",
                        "titles": article_title,
                        "prop": "extracts|pageimages",
                        "exintro": "true",
                        "explaintext": "true",
                        "format": "json",
                        "piprop": "thumbnail",
                        "pithumbsize": "200",
                    },
                    headers=headers
                )
                content_response.raise_for_status()
                content_data = content_response.json()
                
                # Extract page content
                pages = content_data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    extract = page_info.get("extract", "")
                    
                    if extract:
                        full_text = extract
                        # Split into paragraphs and create facts
                        paragraphs = [p.strip() for p in extract.split("\n") if p.strip()]
                        
                        for idx, paragraph in enumerate(paragraphs[:limit * 2]):  # Get more to filter
                            # Get first sentence as title
                            sentences = paragraph.split(".")
                            title = sentences[0][:80].strip() if sentences else "Információ"
                            
                            facts.append(CityFact(
                                title=title,
                                content=paragraph
                            ))
                        
                        break
                
                # Step 3: Filter by activity if provided
                if activity and facts and full_text:
                    filtered_facts = await self._filter_facts_by_activity(city, activity, full_text)
                    return filtered_facts[:limit] if filtered_facts else facts[:limit]
                
                return facts[:limit]
                
        except Exception as e:
            print(f"⚠️ Wikipedia API error: {e}")
            return []
    
    async def _filter_facts_by_activity(self, city: str, activity: str, full_text: str) -> list[CityFact]:
        """Filter facts by activity using LLM."""
        try:
            from ..llm.openai_llm import OpenAIClient
            llm = OpenAIClient()
            
            # Get activity-relevant information fragments
            relevant_fragments = await llm.filter_facts_by_activity(city, activity, full_text)
            
            if not relevant_fragments:
                return []
            
            # Convert fragments to CityFact objects
            filtered_facts = [
                CityFact(
                    title=f"Releváns wikipedia sorok a keresett szöveghez, ami: {activity}",
                    content=fragment
                )
                for fragment in relevant_fragments
            ]
            
            return filtered_facts
        except Exception as e:
            print(f"⚠️ Hiba az információk szűrésében: {e}")
            return []
