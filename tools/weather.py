import requests
import os
from typing import Optional
from geopy.geocoders import Nominatim
from .factory import tool_factory


@tool_factory.register_tool(
    name="get_weather",
    description="Get current weather conditions for a location (city/country/coordinates)",
)
def get_weather(location: str, api_key: Optional[str] = None) -> str:
    api_key = api_key or os.getenv("OPENWEATHER_API_KEY")

    try:
        geolocator = Nominatim(user_agent="weather_finder")
        location_obj = geolocator.geocode(location)
        if not location_obj:
            return f"Could not find location: {location}"

        params = {
            "lat": location_obj.latitude,
            "lon": location_obj.longitude,
            "appid": api_key,
            "units": "metric",
        }

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather", params=params
        )
        response.raise_for_status()
        data = response.json()

        weather_info = {
            "location": location_obj.address,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "conditions": data["weather"][0]["description"],
            "humidity": f"{data['main']['humidity']}%",
            "wind": f"{data['wind']['speed']} m/s",
            "pressure": f"{data['main']['pressure']} hPa",
        }

        return (
            f"Weather in {weather_info['location']}:\n"
            f"- Temperature: {weather_info['temperature']}°C (feels like {weather_info['feels_like']}°C)\n"
            f"- Conditions: {weather_info['conditions']}\n"
            f"- Humidity: {weather_info['humidity']}\n"
            f"- Wind: {weather_info['wind']}\n"
            f"- Pressure: {weather_info['pressure']}"
        )

    except requests.exceptions.RequestException as e:
        return f"Weather API error: {str(e)}"
    except Exception as e:
        return f"Error getting weather for {location}: {str(e)}"
