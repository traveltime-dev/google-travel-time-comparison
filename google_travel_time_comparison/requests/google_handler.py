import logging
from datetime import datetime

import aiohttp
from aiolimiter import AsyncLimiter
from traveltimepy import Coordinates

from google_travel_time_comparison.config import Mode
from google_travel_time_comparison.requests.base_handler import BaseRequestHandler

logger = logging.getLogger(__name__)


class GoogleApiError(Exception):
    pass


class GoogleRequestHandler(BaseRequestHandler):
    DURATION_IN_TRAFFIC = "duration_in_traffic"
    DURATION = "duration"
    GOOGLE_DIRECTIONS_URL = 'https://maps.googleapis.com/maps/api/directions/json'

    def __init__(self, api_key, max_rpm):
        self.api_key = api_key
        self._rate_limiter = AsyncLimiter(max_rpm//60, 1)

    async def send_request(self, origin: Coordinates, destination: Coordinates, departure_time: datetime, mode: Mode):

        params = {
            'origin': "{},{}".format(origin.lat, origin.lng),
            'destination': "{},{}".format(destination.lat, destination.lng),
            'mode': get_google_specific_mode(mode),
            "traffic_model": "best_guess",
            "departure_time": int(departure_time.timestamp()),
            'key': self.api_key
        }

        async with aiohttp.ClientSession() as session, session.get(self.GOOGLE_DIRECTIONS_URL,
                                                                   params=params) as response:
            data = await response.json()

            if data["status"] == "OK":
                route = data.get("routes", [{}])[0]
                leg = route.get("legs", [{}])[0]

                if not leg:
                    raise GoogleApiError("No route found between origin and destination.")

                travel_time = leg.get(self.DURATION_IN_TRAFFIC, leg.get(self.DURATION))["value"]
                distance = leg["distance"]["value"]
                return travel_time, distance
            else:
                logger.error("Error in Google API response: %s", data["status"])
                raise GoogleApiError(data)


def get_google_specific_mode(mode: Mode) -> str:
    if mode == Mode.DRIVING:
        return "driving"
    elif mode == Mode.PUBLIC_TRANSPORT:
        return "transit"
    else:
        raise ValueError(f"Unsupported mode: `{mode.value}`")
