"""LangGraph-based agent with tool nodes for API calls."""
from datetime import date
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger

from app.domain.interfaces import (
    GeocodingService,
    WeatherService,
)
from app.domain.models import Briefing, BriefingResponse, Location, UserProfile, WeatherData


class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    city: str
    target_date: date
    user_profile: Optional[UserProfile]
    language: str | None
    location: Location | None
    weather: WeatherData | None
    briefing: Briefing | None
    final_response: BriefingResponse | None


class LangGraphWeatherAgent:
    """Weather briefing agent using LangGraph for orchestration."""

    def __init__(
        self,
        geocoding_service: GeocodingService,
        weather_service: WeatherService,
        llm_api_key: str,
        llm_model: str,
    ):
        """
        Initialize LangGraph weather agent.

        Args:
            geocoding_service: Service for geocoding
            weather_service: Service for weather data
            llm_api_key: OpenAI API key
            llm_model: Model name to use
        """
        self.geocoding_service = geocoding_service
        self.weather_service = weather_service
        self.llm = ChatOpenAI(
            api_key=llm_api_key,
            model=llm_model,
            temperature=0.7,
        )

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("geocode", self._geocode_node)
        workflow.add_node("fetch_weather", self._fetch_weather_node)
        workflow.add_node("generate_briefing", self._generate_briefing_node)
        workflow.add_node("finalize", self._finalize_node)

        # Define edges
        workflow.set_entry_point("geocode")
        workflow.add_edge("geocode", "fetch_weather")
        workflow.add_edge("fetch_weather", "generate_briefing")
        workflow.add_edge("generate_briefing", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _geocode_node(self, state: AgentState) -> AgentState:
        """
        Node: Geocode the city to get coordinates.

        Args:
            state: Current agent state

        Returns:
            Updated state with location
        """
        logger.info(f"[GEOCODE NODE] Processing city: {state['city']}")

        try:
            location = await self.geocoding_service.geocode(state["city"])
            logger.info(
                f"[GEOCODE NODE] Success: {location.city}, {location.country} "
                f"({location.coordinates.lat}, {location.coordinates.lon})"
            )

            state["location"] = location
            state["messages"].append(
                SystemMessage(
                    content=f"Geocoded {state['city']} to {location.city}, "
                    f"{location.country} at coordinates "
                    f"({location.coordinates.lat}, {location.coordinates.lon})"
                )
            )
        except Exception as e:
            logger.error(f"[GEOCODE NODE] Failed: {e}")
            raise

        return state

    async def _fetch_weather_node(self, state: AgentState) -> AgentState:
        """
        Node: Fetch weather data for the location and date.

        Args:
            state: Current agent state

        Returns:
            Updated state with weather data
        """
        location = state["location"]
        if not location:
            raise ValueError("Location not available")

        logger.info(
            f"[WEATHER NODE] Fetching weather for "
            f"{location.coordinates.lat}, {location.coordinates.lon} "
            f"on {state['target_date']}"
        )

        try:
            weather = await self.weather_service.get_weather(
                location.coordinates.lat,
                location.coordinates.lon,
                state["target_date"],
            )
            logger.info(
                f"[WEATHER NODE] Success: {weather.temperature_min}-"
                f"{weather.temperature_max}°C, {weather.precipitation_probability}% rain"
            )

            state["weather"] = weather
            state["messages"].append(
                SystemMessage(
                    content=f"Weather forecast: {weather.temperature_min}-"
                    f"{weather.temperature_max}°C, wind {weather.wind_speed} m/s, "
                    f"{weather.precipitation_probability}% precipitation"
                )
            )
        except Exception as e:
            logger.error(f"[WEATHER NODE] Failed: {e}")
            raise

        return state

    async def _generate_briefing_node(self, state: AgentState) -> AgentState:
        """
        Node: Generate AI briefing using LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state with briefing
        """
        location = state["location"]
        weather = state["weather"]
        user_profile = state.get("user_profile")

        if not location or not weather:
            raise ValueError("Location or weather data not available")

        logger.info(
            f"[BRIEFING NODE] Generating AI briefing"
            + (" (personalized)" if user_profile else " (generic)")
        )

        days_ahead = (state["target_date"] - date.today()).days

        # Build personalization context
        personalization = ""
        if user_profile:
            parts = []
            if user_profile.age:
                parts.append(f"Age: {user_profile.age}")
            if user_profile.interests:
                parts.append(f"Interests: {', '.join(user_profile.interests)}")
            if user_profile.mobility:
                parts.append(f"Mobility: {user_profile.mobility}")
            if user_profile.clothing_style:
                parts.append(f"Style: {user_profile.clothing_style}")
            if user_profile.dietary_preferences:
                parts.append(
                    f"Dietary: {', '.join(user_profile.dietary_preferences)}"
                )

            if parts:
                personalization = f"\n\nUser Profile:\n- " + "\n- ".join(parts)

        # Get language instruction
        language = state.get("language") or "en"
        language_instruction = ""
        if language and language != "en":
            language_names = {
                "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
                "pt": "Portuguese", "nl": "Dutch", "pl": "Polish", "ru": "Russian",
                "ja": "Japanese", "zh": "Chinese", "ko": "Korean", "ar": "Arabic",
                "hi": "Hindi", "hu": "Hungarian"
            }
            lang_name = language_names.get(language, language)
            language_instruction = f"\n\nIMPORTANT: Respond in {lang_name}. All text (summary, outfit, activities) must be in {lang_name}."

        prompt = f"""You are a weather day-planner AI assistant with local knowledge.

City: {location.city} ({location.country})
Date: {state['target_date'].isoformat()}
Weather: min {weather.temperature_min}°C, max {weather.temperature_max}°C, wind {weather.wind_speed} m/s, precipitation probability {weather.precipitation_probability}%
{personalization}{language_instruction}

Task:
- Write a short 1–2 sentence weather summary.
- Provide concise outfit advice{' tailored to the user profile' if user_profile else ''}.
- Suggest exactly 3 **SPECIFIC** activities with REAL venue names and addresses in {location.city}:
  * At least 1 outdoor activity (with specific location/park/area name)
  * At least 1 indoor activity (specific café/restaurant/museum/theater with name and address)
  * Each suggestion MUST include: venue name, street address, and brief reason why
  * {'Match venues to user interests (e.g., vegan restaurants for vegan dietary preferences, live music venues for music interests)' if user_profile else 'Choose popular, well-known venues'}
{"- Add a one-sentence uncertainty note since the forecast is " + str(days_ahead) + " days ahead." if days_ahead > 7 else ""}

IMPORTANT: Do NOT give generic suggestions like "Visit a local café" or "Check out a theater". 
Instead, provide REAL venues like "Café de Jaren (Nieuwe Doelenstraat 20) - cozy spot with canal views and vegan options".

Return **strict JSON** in the following schema:
{{
  "summary": string,
  "outfit": string,
  "activities": [string, string, string],
  "note": string | null
}}
"""

        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="You are a helpful weather assistant that provides "
                        "briefings in strict JSON format."
                    ),
                    HumanMessage(content=prompt),
                ],
                response_format={"type": "json_object"},
            )

            import json

            briefing_data = json.loads(response.content)
            briefing = Briefing(**briefing_data)

            logger.info(f"[BRIEFING NODE] Success: Generated briefing with {len(briefing.activities)} activities")

            state["briefing"] = briefing
            state["messages"].append(
                SystemMessage(content=f"Generated personalized briefing")
            )
        except Exception as e:
            logger.error(f"[BRIEFING NODE] Failed: {e}")
            raise

        return state

    async def _finalize_node(self, state: AgentState) -> AgentState:
        """
        Node: Finalize the response.

        Args:
            state: Current agent state

        Returns:
            Updated state with final response
        """
        from datetime import datetime

        location = state["location"]
        weather = state["weather"]
        briefing = state["briefing"]

        if not location or not weather or not briefing:
            raise ValueError("Missing required data for finalization")

        logger.info(f"[FINALIZE NODE] Creating final response")

        final_response = BriefingResponse(
            city=location.city,
            country=location.country,
            coordinates=location.coordinates,
            date=state["target_date"],
            weather=weather,
            briefing=briefing,
            timestamp=datetime.utcnow(),
        )

        state["final_response"] = final_response
        state["messages"].append(SystemMessage(content="Briefing complete"))

        logger.info(f"[FINALIZE NODE] Success: Briefing ready")

        return state

    async def run(
        self, city: str, target_date: date, user_profile: Optional[UserProfile] = None, language: str | None = None
    ) -> BriefingResponse:
        """
        Execute the agent workflow.

        Args:
            city: City name
            target_date: Target date for weather
            user_profile: Optional user profile for personalization
            language: Language code for the response (e.g., 'en', 'es', 'fr')

        Returns:
            Complete briefing response
        """
        logger.info(f"[AGENT] Starting workflow for {city} on {target_date} (language: {language or 'en'})")

        initial_state: AgentState = {
            "messages": [
                HumanMessage(
                    content=f"Generate a weather briefing for {city} on {target_date}"
                )
            ],
            "city": city,
            "target_date": target_date,
            "user_profile": user_profile,
            "language": language,
            "location": None,
            "weather": None,
            "briefing": None,
            "final_response": None,
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        if not final_state.get("final_response"):
            raise ValueError("Agent failed to produce final response")

        logger.info(f"[AGENT] Workflow complete")

        return final_state["final_response"]
