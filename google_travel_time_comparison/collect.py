import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd
import pytz
from pandas import DataFrame
from pytz.tzinfo import StaticTzInfo, DstTzInfo
from traveltimepy import Coordinates

from google_travel_time_comparison.config import Mode
from google_travel_time_comparison.requests.base_handler import BaseRequestHandler

GOOGLE_API = "google"
TRAVELTIME_API = "traveltime"


@dataclass
class Fields:
    ORIGIN = "origin"
    DESTINATION = "destination"
    DEPARTURE_TIME = "departure_time"
    TRAVEL_TIME = {
        GOOGLE_API: "google_time",
        TRAVELTIME_API: "traveltime_time"
    }
    DISTANCE = {
        GOOGLE_API: "google_distance",
        TRAVELTIME_API: "traveltime_distance"
    }


logger = logging.getLogger(__name__)


async def fetch_travel_time_and_distance(
        origin: str, destination: str, api: str, departure_time: datetime,
        request_handler: BaseRequestHandler, mode: Mode) -> dict[str, str]:
    origin_coord = parse_coordinates(origin)
    destination_coord = parse_coordinates(destination)

    async with request_handler.rate_limiter:
        logger.debug(f"Sending request to {api} for {origin_coord}, {destination_coord}, {departure_time}")
        travel_time, distance = await request_handler.send_request(origin_coord, destination_coord, departure_time,
                                                                   mode)
        logger.debug(f"Finished request to {api} for {origin_coord}, {destination_coord}, {departure_time}")
        return wrap_result(origin, destination, travel_time, distance, departure_time, api)


def parse_coordinates(coord_string: str) -> Coordinates:
    lat, lng = coord_string.split(",")
    return Coordinates(lat=lat, lng=lng)


def wrap_result(origin: str, destination: str, travel_time: int, distance: int, departure_time: datetime, api: str):
    return {
        Fields.ORIGIN: origin,
        Fields.DESTINATION: destination,
        Fields.DEPARTURE_TIME: departure_time.strftime("%Y-%m-%d %H:%M:%S%z"),
        Fields.TRAVEL_TIME[api]: travel_time,
        Fields.DISTANCE[api]: distance
    }


def localize_datetime(date: str, time: str, timezone: StaticTzInfo | DstTzInfo) -> datetime:
    datetime_instance = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    return timezone.localize(datetime_instance)


def generate_tasks(data: DataFrame, time_instants: List[datetime],
                   request_handlers: Dict[str, BaseRequestHandler], mode: Mode) -> list:
    tasks = []
    for index, row in data.iterrows():
        for time_instant in time_instants:
            for api, request_handler in request_handlers.items():
                task = fetch_travel_time_and_distance(row[Fields.ORIGIN], row[Fields.DESTINATION], api, time_instant,
                                                      request_handler, mode=mode)
                tasks.append(task)
    return tasks


async def collect_travel_times(args, data, request_handlers: Dict[str, BaseRequestHandler]) -> DataFrame:
    timezone = pytz.timezone(args.time_zone_id)
    localized_start_datetime = localize_datetime(args.date, args.start_time, timezone)
    localized_end_datetime = localize_datetime(args.date, args.end_time, timezone)
    time_instants = generate_time_instants(localized_start_datetime, localized_end_datetime,
                                           args.interval)

    tasks = generate_tasks(data, time_instants, request_handlers, mode=Mode(args.mode))

    logger.info(
        f"Sending {len(tasks)} requests to Google and TravelTime APIs")

    results = await asyncio.gather(*tasks)

    results_df = pd.DataFrame(results)
    deduplicated = results_df.groupby([Fields.ORIGIN, Fields.DESTINATION, Fields.DEPARTURE_TIME], as_index=False).agg(
        {
            Fields.TRAVEL_TIME[GOOGLE_API]: 'first',
            Fields.DISTANCE[GOOGLE_API]: 'first',
            Fields.TRAVEL_TIME[TRAVELTIME_API]: 'first',
            Fields.DISTANCE[TRAVELTIME_API]: 'first'
        }
    )
    deduplicated.to_csv(args.output, index=False)
    return deduplicated


def generate_time_instants(start_time: datetime, end_time: datetime, interval: int) -> List[datetime]:
    if start_time > end_time:
        raise ValueError("Start time must be before end time.")
    current_time = start_time
    results = []
    while current_time <= end_time:
        results.append(current_time)
        current_time += timedelta(minutes=interval)
    return results
