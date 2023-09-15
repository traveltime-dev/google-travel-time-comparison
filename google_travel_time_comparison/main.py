import asyncio
import logging

import pandas as pd

from google_travel_time_comparison import collect
from google_travel_time_comparison import config
from google_travel_time_comparison.analysis import run_analysis
from google_travel_time_comparison.collect import Fields, GOOGLE_API, TRAVELTIME_API
from google_travel_time_comparison.requests import factory


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


async def main():
    args = config.parse_args()
    csv = pd.read_csv(args.input, usecols=[Fields.ORIGIN, Fields.DESTINATION]).drop_duplicates()

    request_handlers = factory.initialize_request_handlers(args.google_max_rpm, args.traveltime_max_rpm)
    if args.skip_data_gathering:
        travel_times = pd.read_csv(args.input, usecols=[Fields.ORIGIN, Fields.DESTINATION, Fields.DEPARTURE_TIME,
                                                        Fields.TRAVEL_TIME[GOOGLE_API],
                                                        Fields.TRAVEL_TIME[TRAVELTIME_API]])
    else:
        travel_times = await collect.collect_travel_times(args, csv, request_handlers)
    run_analysis(travel_times, args.output, [0.9, 0.95, 0.99])


if __name__ == "__main__":
    asyncio.run(main())
