from geopy.geocoders import Nominatim
from .factory import tool_factory


@tool_factory.register_tool(
    name="location_converter",
    description="Convert between geographic coordinates and city names. Input can be either coordinates (lat,lon) or location name.",
)
def location_converter(location: str) -> str:
    geolocator = Nominatim(user_agent="location_converter")

    try:
        if "," in location and all(
            part.strip().replace(".", "").replace("-", "").isdigit()
            for part in location.split(",")
        ):
            lat, lon = map(float, location.split(","))
            location_obj = geolocator.reverse(f"{lat}, {lon}")
            return (
                f"Coordinates {location} correspond to: {location_obj.address}"
                if location_obj
                else f"No location found for coordinates {location}"
            )

        location_obj = geolocator.geocode(location)
        return (
            f"{location} is at coordinates: {location_obj.latitude},{location_obj.longitude}"
            if location_obj
            else f"Could not find coordinates for location: {location}"
        )

    except Exception as e:
        return f"Error converting location: {str(e)}"
