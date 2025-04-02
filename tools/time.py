from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from .factory import tool_factory


@tool_factory.register_tool(
    name="get_time",
    description="Get current time in any location (city/country/coordinates)",
)
def get_time(location: str) -> str:
    try:
        try:
            tz = pytz.timezone(location)
            current_time = datetime.now(tz)
            return f"Current time in {location}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except pytz.UnknownTimeZoneError:
            pass

        geolocator = Nominatim(user_agent="time_finder")
        location_obj = geolocator.geocode(location)

        if location_obj:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(
                lng=location_obj.longitude, lat=location_obj.latitude
            )

            if timezone_str:
                tz = pytz.timezone(timezone_str)
                current_time = datetime.now(tz)
                return (
                    f"Current time in {location_obj.address}: "
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"(Timezone: {timezone_str})"
                )

        current_time = datetime.now(pytz.UTC)
        return (
            f"Couldn't determine timezone for {location}. "
            f"UTC time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    except Exception as e:
        return f"Error getting time for {location}: {str(e)}"
