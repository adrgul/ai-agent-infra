"""
Main entry point: Meeting Assistant Agent
Felhasználó interakció, agent döntés, API meghívás
"""
import sys
import os
from dotenv import load_dotenv

# Töltsd be a .env fájl változóit
load_dotenv()

# Adjuk hozzá a src mappát az import path-hez
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import MeetingAssistantAgent
from api_clients import WeatherClient, TimezoneClient, CountryClient, GeocodeClient, IPGeolocationClient
from formatters import (
    format_weather,
    format_timezone,
    format_country,
    format_coordinates,
    format_my_location,
    format_error,
)


class MeetingAssistant:
    """
    Fő agent: user inputot feldolgozza, API-t hív meg, szép kimenetet ad.
    """

    def __init__(self, openweather_key: str = ""):
        self.agent = MeetingAssistantAgent()
        self.weather_client = WeatherClient(api_key=openweather_key)
        self.timezone_client = TimezoneClient()
        self.country_client = CountryClient()
        self.geocode_client = GeocodeClient()
        self.ip_geolocation_client = IPGeolocationClient()

    def execute_action(self, parsed_input: dict) -> str:
        """
        Végrehajt egy action-t az agent döntése alapján.

        Args:
            parsed_input: dict az agent.parse_input() eredménye

        Returns:
            str: Formázott kimenet
        """
        action = parsed_input.get("action")
        params = parsed_input.get("params", {})
        location = params.get("location", "")

        # Hibakezelés
        if "error" in parsed_input:
            return format_error(parsed_input["error"])

        # Action végrehajtas
        if action == "weather":
            response = self.weather_client.get_weather(location)
            return format_weather(response)

        elif action == "timezone":
            response = self.timezone_client.get_timezone_by_city(location)
            return format_timezone(response)

        elif action == "country":
            response = self.country_client.get_country_info(location)
            return format_country(response)

        elif action == "location":
            response = self.geocode_client.get_coordinates(location)
            return format_coordinates(response)

        elif action == "myip":
            response = self.ip_geolocation_client.get_my_location()
            return format_my_location(response)

        else:
            return format_error("Ismeretlen parancs.")

    def process_input(self, user_input: str) -> str:
        """
        Feldolgozza a user inputot: parse → validate → execute.

        Args:
            user_input: User által beírt szöveg

        Returns:
            str: Kimenet
        """
        # Parse
        parsed = self.agent.parse_input(user_input)

        # Validate
        validated = self.agent.validate_action(parsed)

        # Execute
        return self.execute_action(validated)

    def run(self):
        """
        Interaktív hurok: user inputot kér, feldolgozza, kiírja az eredményt.
        """
        print("\n" + "=" * 50)
        print("🤖 Meeting Assistant - Info Gyűjtő Agent")
        print("=" * 50)
        print("\n📋 Parancsok:")
        print("  • country [ország]   - Ország adatai ✅")
        print("  • location [hely]    - Koordináták ✅")
        print("  • myip               - Az Ön helye (IP alapján) ✅")
        print("  • weather [város]    - Időjárás lekérdezés ✅")
        print("  • timezone [város]   - Időzóna információ")
        print("  • exit / quit        - Kilépés")
        print("\n📝 Munkavégzett Parancsok:")
        print("  > country Hungary")
        print("  > location Eiffel Tower")
        print("  > myip")
        print("  > weather Budapest")
        print("\n" + "=" * 50 + "\n")

        while True:
            try:
                user_input = input("🤖 > ").strip()

                if not user_input:
                    continue

                # Kilépés
                if user_input.lower() in ["exit", "quit", "kilépés"]:
                    print("\n👋 Viszlát!")
                    break

                # Feldolgozás és kimenet
                result = self.process_input(user_input)
                print(f"\n{result}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Viszlát!")
                break
            except Exception as e:
                print(f"\n❌ Váratlan hiba: {str(e)}\n")


def main():
    """
    Entry point.
    """
    # OpenWeatherMap API key (Environment variable-ből vagy .env fájlból)
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")

    assistant = MeetingAssistant(openweather_key=api_key)
    assistant.run()


if __name__ == "__main__":
    main()
