"""
Mini-agent logika: user input → API döntés
"""
import re
from typing import Dict, Any


class MeetingAssistantAgent:
    """
    Felismeri a user inputot és dönt, melyik API-t kell meghívni.
    """

    # Kulcsszó → API action leképezés
    ACTION_KEYWORDS = {
        "weather": {
            "keywords": ["weather", "időjárás", "temp", "hőmérséklet", "felhő"],
            "action": "weather",
        },
        "timezone": {
            "keywords": ["timezone", "time", "óra", "időzóna", "tz"],
            "action": "timezone",
        },
        "country": {
            "keywords": ["country", "ország", "capital", "főváros", "flag"],
            "action": "country",
        },
        "location": {
            "keywords": ["location", "hely", "cím", "coordinates", "koord"],
            "action": "location",
        },
        "myip": {
            "keywords": ["myip", "ip", "whereami", "hol vagyok", "geolocation", "geolocate"],
            "action": "myip",
        },
    }

    def parse_input(self, user_input: str) -> Dict[str, Any]:
        """
        Elemzi a user inputot és meghatározza az action-t és paramétereket.

        Args:
            user_input: User által beírt szöveg (pl. "weather Budapest")

        Returns:
            dict: {"action": str, "params": dict, "raw_input": str}
        """
        user_input = user_input.strip().lower()

        # Action felismerése
        action = None
        for key, config in self.ACTION_KEYWORDS.items():
            for keyword in config["keywords"]:
                if keyword in user_input:
                    action = config["action"]
                    break
            if action:
                break

        if not action:
            return {
                "action": "unknown",
                "params": {},
                "raw_input": user_input,
                "error": "Nem értem a parancsot. Próbáld: 'weather [város]', 'timezone [város]', 'country [ország]'",
            }

        # Paraméter kinyerése (város/ország név)
        # Pl. "weather Budapest" → {"city": "Budapest"}
        parts = user_input.split()
        
        # Az első keyword után jövő szó(k) a paraméter
        location = None
        for i, part in enumerate(parts):
            is_keyword = False
            for config in self.ACTION_KEYWORDS.values():
                if part in config["keywords"]:
                    is_keyword = True
                    # Az első szó után jövő elem a város/ország
                    if i + 1 < len(parts):
                        location = " ".join(parts[i + 1 :])
                    break
            if is_keyword:
                break

        return {
            "action": action,
            "params": {"location": location} if location else {},
            "raw_input": user_input,
        }

    def validate_action(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validálja, hogy az action-hez szükséges paraméterek megvannak-e.
        """
        if parsed["action"] == "unknown":
            return parsed

        # myip action-hez nem szükséges paraméter
        if parsed["action"] == "myip":
            return parsed

        if not parsed["params"].get("location"):
            return {
                **parsed,
                "error": f"Hiányzik a paraméter! Pl.: '{parsed['action']} Budapest'",
            }

        return parsed
