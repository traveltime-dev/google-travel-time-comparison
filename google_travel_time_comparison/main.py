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

logger = logging.getLogger(__name__)


async def run():
    args = config.parse_args()
    csv = pd.read_csv(args.input, usecols=[Fields.ORIGIN, Fields.DESTINATION]).drop_duplicates()

    request_handlers = factory.initialize_request_handlers(args.google_max_rpm, args.traveltime_max_rpm)
    if args.skip_data_gathering:
        travel_times_df = pd.read_csv(args.input, usecols=[Fields.ORIGIN, Fields.DESTINATION, Fields.DEPARTURE_TIME,
                                                        Fields.TRAVEL_TIME[GOOGLE_API],
                                                        Fields.TRAVEL_TIME[TRAVELTIME_API]])
    else:
        travel_times_df = await collect.collect_travel_times(args, csv, request_handlers)
    filtered_travel_times_df = travel_times_df.loc[travel_times_df[Fields.TRAVEL_TIME[GOOGLE_API]].notna() & travel_times_df[Fields.TRAVEL_TIME[TRAVELTIME_API]].notna(), :]
    
    N, n = travel_times_df.shape[0], filtered_travel_times_df.shape[0]
    logger.info(f"Skipped {N-n}/{N} rows ({100*(N-n)/N:.2f}%)")
    run_analysis(filtered_travel_times_df, args.output, [0.9, 0.95, 0.99])


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
