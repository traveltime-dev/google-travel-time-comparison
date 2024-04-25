from datetime import datetime
from typing import Tuple, Union

from aiolimiter import AsyncLimiter
from traveltimepy import Location, Coordinates, TravelTimeSdk, Driving, Property, PublicTransport
from traveltimepy.dto.common import SnapPenalty

from google_travel_time_comparison.config import Mode
from google_travel_time_comparison.requests.base_handler import BaseRequestHandler


class TravelTimeRequestHandler(BaseRequestHandler):

    ORIGIN_ID = "o"
    DESTINATION_ID = "d"

    def __init__(self, app_id, api_key, max_rpm):
        self.sdk = TravelTimeSdk(app_id, api_key)
        self._rate_limiter = AsyncLimiter(max_rpm//60, 1)

    async def send_request(
            self,
            origin: Coordinates,
            destination: Coordinates,
            departure_time: datetime,
            mode: Mode
    ) -> Tuple[int, int]:
        locations = [
            Location(id=self.ORIGIN_ID, coords=origin),
            Location(id=self.DESTINATION_ID, coords=destination),
        ]

        results = await self.sdk.routes_async(
            locations=locations,
            search_ids={
                self.ORIGIN_ID: [self.DESTINATION_ID],
            },
            transportation=get_traveltime_specific_mode(mode),
            departure_time=departure_time,
            properties=[Property.TRAVEL_TIME, Property.DISTANCE],
            snap_penalty=SnapPenalty.DISABLED
        )

        if not results or not results[0].locations or not results[0].locations[0].properties:
            raise RouteNotFoundError("No route found between the provided origin and destination.")

        properties = results[0].locations[0].properties[0]
        return properties.travel_time, properties.distance


class RouteNotFoundError(Exception):
    pass


def get_traveltime_specific_mode(mode: Mode) -> Union[Driving, PublicTransport]:
    if mode.value == Mode.DRIVING.value:
        return Driving()
    elif mode.value == Mode.PUBLIC_TRANSPORT.value:
        return PublicTransport()
    else:
        raise ValueError(f"Unsupported mode `{mode.value}`")
