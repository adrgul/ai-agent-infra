print("=== SCRIPT STARTED ===")
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENW_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENW_API_KEY not found in .env file")

# Example request parameters
city = "Budapest"
url = "https://api.openweathermap.org/data/2.5/weather"
params = {
    "q": city,
    "appid": API_KEY,
    "units": "metric"
}

#print("API key loaded:", API_KEY[:5], "...") -> to test if key is loaded correctly

response = requests.get(url, params=params, timeout=10)

response.raise_for_status()

data = response.json()

print(f"Weather in {city}:")
print("Temperature:", data["main"]["temp"], "°C")
print("Description:", data["weather"][0]["description"])

print("=== SCRIPT ENDED ===")
