from typing import Dict, Callable, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import requests
from typing import Optional

class ToolFactory:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, str] = {}

    def register_tool(self, name: str, description: str = "") -> Callable:
        """Decorator to register a new tool"""

        def decorator(func: Callable) -> Callable:
            # Create the LangChain tool with proper metadata
            func.__name__ = name
            func.__doc__ = description
            tool_func = tool(func)

            # Store both the original function and the tool
            self._tools[name] = tool_func
            self._tool_descriptions[name] = description

            return tool_func

        return decorator

    def get_tools(self) -> list:
        """Get all registered tools as LangChain tools"""
        return list(self._tools.values())

    def invoke_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Invoke a registered tool by name"""
        if tool_name not in self._tools:
            raise ValueError(f"Tool {tool_name} not registered")
        return self._tools[tool_name].invoke(args)


# Create a global tool factory instance
tool_factory = ToolFactory()


@tool_factory.register_tool(
    name="location_converter",
    description="Convert between geographic coordinates and city names. Input can be either coordinates (lat,lon) or location name."
)
def location_converter(location: str) -> str:
    print(f"CONVERT LOCATION for {location}...")
    """
    Convert between geographic coordinates and location names bidirectionally.

    Args:
        location (str): Either:
            - Coordinates in "latitude,longitude" format (e.g., "48.8566,2.3522")
            - Location name (e.g., "Paris, France")

    Returns:
        str: Conversion result in the format:
            - If input was coordinates: "Coordinates 48.8566,2.3522 correspond to: [full address]"
            - If input was location name: "[Location name] is at coordinates: latitude,longitude"
    """
    geolocator = Nominatim(user_agent="location_converter")

    try:
        # Check if input is coordinates
        if "," in location and all(
                part.strip().replace(".", "").replace("-", "").isdigit() for part in location.split(",")):
            lat, lon = map(float, location.split(","))
            location_obj = geolocator.reverse(f"{lat}, {lon}")

            if location_obj:
                return f"Coordinates {location} correspond to: {location_obj.address}"
            else:
                return f"No location found for coordinates {location}"

        # Otherwise treat as location name
        else:
            location_obj = geolocator.geocode(location)

            if location_obj:
                return f"{location} is at coordinates: {location_obj.latitude},{location_obj.longitude}"
            else:
                return f"Could not find coordinates for location: {location}"

    except Exception as e:
        return f"Error converting location: {str(e)}"

@tool_factory.register_tool(
    name="get_weather",
    description="Get current weather conditions for a location (city/country/coordinates)"
)
def get_weather(location: str, api_key: Optional[str] = None) -> str:
    print(f"GET WEATHER for {location}...")
    """
    Get detailed weather information for a location using OpenWeatherMap API.

    Args:
        location (str): Can be:
            - City name (e.g., "Paris")
            - Country name (e.g., "Japan")
            - Coordinates (e.g., "48.8566,2.3522")
        api_key (str, optional): OpenWeatherMap API key. If not provided, uses a demo key.

    Returns:
        str: Formatted weather information including temperature, conditions, humidity, etc.
    """
    # Use a demo API key if none provided (note: demo keys have limits)
    api_key = api_key or "42e8259aa7ef3355a6228581a57215e0"  # This is a free demo key

    try:
        # First try direct geocoding
        geolocator = Nominatim(user_agent="weather_finder")
        location_obj = geolocator.geocode(location)

        if not location_obj:
            return f"Could not find location: {location}"

        # Get weather data from OpenWeatherMap
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': location_obj.latitude,
            'lon': location_obj.longitude,
            'appid': api_key,
            'units': 'metric'  # Get temperature in Celsius
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract and format weather information
        weather_info = {
            'location': location_obj.address,
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'conditions': data['weather'][0]['description'],
            'humidity': f"{data['main']['humidity']}%",
            'wind': f"{data['wind']['speed']} m/s",
            'pressure': f"{data['main']['pressure']} hPa"
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


@tool_factory.register_tool(
    name="get_time",
    description="Get current time in any location (city/country/coordinates)"
)
def get_time(location: str) -> str:
    print(f"GET TIME for {location}...")
    """
    Get current time for any location in the world.

    Args:
        location (str): Can be:
            - City name (e.g., "Paris")
            - Country name (e.g., "Japan")
            - Coordinates (e.g., "48.8566,2.3522")
            - Timezone name (e.g., "Europe/Paris")

    Returns:
        str: Formatted current time with location info
    """
    try:
        # First try direct timezone lookup
        try:
            tz = pytz.timezone(location)
            current_time = datetime.now(tz)
            return f"Current time in {location}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except pytz.UnknownTimeZoneError:
            pass

        # Try to geocode the location
        geolocator = Nominatim(user_agent="time_finder")
        location_obj = geolocator.geocode(location)

        if location_obj:
            # Find timezone from coordinates
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(
                lng=location_obj.longitude,
                lat=location_obj.latitude
            )

            if timezone_str:
                tz = pytz.timezone(timezone_str)
                current_time = datetime.now(tz)
                return (
                    f"Current time in {location_obj.address}: "
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"(Timezone: {timezone_str})"
                )

        # Fallback to UTC if all else fails
        current_time = datetime.now(pytz.UTC)
        return (
            f"Couldn't determine timezone for {location}. "
            f"UTC time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    except Exception as e:
        return f"Error getting time for {location}: {str(e)}"


def chat_with_recursion(prompt, max_depth=3, current_depth=0, chat=None):
    if current_depth >= max_depth:
        return "Max recursion depth reached"

    if chat is None:
        chat = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key="sk-b917616968c142b188c80b96d4a8b4cd",
            base_url="https://api.deepseek.com"
        ).bind_tools(tool_factory.get_tools())

    # Handle both string and message list cases
    if isinstance(prompt, str):
        messages = [HumanMessage(content=prompt)]
    else:
        messages = prompt  # Already a list of messages

    response = chat.invoke(messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        # Process all tool calls, not just the first one
        tool_messages = []
        for tool_call in response.tool_calls:
            if tool_call["name"] in tool_factory._tools:
                tool_result = tool_factory.invoke_tool(
                    tool_call["name"],
                    tool_call["args"]
                )
                tool_messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    )
                )

        # Include all tool results in the next iteration
        return chat_with_recursion(
            messages + [response] + tool_messages,
            max_depth,
            current_depth + 1,
            chat
        )

    return response.content


# Example usage
# result = chat_with_recursion("Find out coordinates of `КИЕВ` and find out current TIME and WEATHER by coordinates")
# print(result)

result = chat_with_recursion("Шо по погоде в Киеве?")
print(result)

result = chat_with_recursion("А завтра какая погода будет в Киеве?")
print(result)