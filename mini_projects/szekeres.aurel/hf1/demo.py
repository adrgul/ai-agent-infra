#!/usr/bin/env python3
"""
Demo script - Meeting Assistant tesztelése
Beépített tesztkérések
"""
import sys
import os
from dotenv import load_dotenv

# Töltsd be a .env fájl változóit
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import MeetingAssistantAgent
from src.api_clients import (
    WeatherClient,
    TimezoneClient,
    CountryClient,
    GeocodeClient,
    IPGeolocationClient,
)
from src.formatters import (
    format_weather,
    format_timezone,
    format_country,
    format_coordinates,
    format_my_location,
    format_error,
)


def run_demo():
    """Demo: előre definiált tesztkérések futtatása."""

    print("=" * 60)
    print("🤖 Meeting Assistant Demo - API Tesztelés")
    print("=" * 60)

    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    agent = MeetingAssistantAgent()
    weather_client = WeatherClient(api_key=api_key)
    timezone_client = TimezoneClient()
    country_client = CountryClient()
    geocode_client = GeocodeClient()
    ip_geolocation_client = IPGeolocationClient()

    # Tesztkérések
    test_inputs = [
        "weather Budapest",
        "country France",
        "location Eiffel Tower",
        "myip",
    ]

    for user_input in test_inputs:
        print(f"\n📝 Input: '{user_input}'")
        print("-" * 60)

        # Parse
        parsed = agent.parse_input(user_input)
        validated = agent.validate_action(parsed)

        if "error" in validated:
            print(format_error(validated["error"]))
            continue

        action = validated["action"]
        location = validated["params"].get("location", "")

        # Execute action
        if action == "weather":
            response = weather_client.get_weather(location)
            print(format_weather(response))

        elif action == "timezone":
            response = timezone_client.get_timezone_by_city(location)
            print(format_timezone(response))

        elif action == "country":
            response = country_client.get_country_info(location)
            print(format_country(response))

        elif action == "location":
            response = geocode_client.get_coordinates(location)
            print(format_coordinates(response))

        elif action == "myip":
            response = ip_geolocation_client.get_my_location()
            print(format_my_location(response))

    print("\n" + "=" * 60)
    print("✅ Demo befejeződött!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
