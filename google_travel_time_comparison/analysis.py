import logging
from dataclasses import dataclass
from typing import List

from pandas import DataFrame

from google_travel_time_comparison.collect import Fields, GOOGLE_API, TRAVELTIME_API

ABSOLUTE_ERROR = "absolute_error"
RELATIVE_ERROR = "relative_error"


@dataclass
class QuantileErrorResult:
    absolute_error: int
    relative_error: int


def run_analysis(results: DataFrame, output_file: str, quantiles: List[float]):
    results_with_differences = calculate_differences(results)
    for q in quantiles:
        quantile_errors = calculate_quantiles(results_with_differences, q)
        logging.info(
            f"{int(q * 100)}% of TravelTime results differ from Google API by less than {int(quantile_errors.absolute_error)}s / {int(quantile_errors.relative_error)}%")

    logging.info(f"Detailed errors and results can be found in {output_file} file")

    results_with_differences.to_csv(output_file, index=False)


def calculate_differences(results: DataFrame) -> DataFrame:
    results_with_differences = results.assign(**{
        ABSOLUTE_ERROR: abs(results[Fields.TRAVEL_TIME[GOOGLE_API]] - results[Fields.TRAVEL_TIME[TRAVELTIME_API]])
    })
    results_with_differences[RELATIVE_ERROR] = (
            results_with_differences[ABSOLUTE_ERROR] / results_with_differences[Fields.TRAVEL_TIME[GOOGLE_API]] * 100
    )
    return results_with_differences


def calculate_quantiles(results_with_differences: DataFrame, quantile: float) -> QuantileErrorResult:
    quantile_absolute_error = results_with_differences[ABSOLUTE_ERROR].quantile(quantile, "higher")
    quantile_relative_error = results_with_differences[RELATIVE_ERROR].quantile(quantile, "higher")
    return QuantileErrorResult(quantile_absolute_error, quantile_relative_error)
