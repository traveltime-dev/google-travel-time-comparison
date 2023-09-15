from typing import Dict

from google_travel_time_comparison.collect import TRAVELTIME_API, GOOGLE_API
from google_travel_time_comparison.config import retrieve_google_api_key, retrieve_traveltime_credentials
from google_travel_time_comparison.requests.base_handler import BaseRequestHandler
from google_travel_time_comparison.requests.google_handler import GoogleRequestHandler
from google_travel_time_comparison.requests.traveltime_handler import TravelTimeRequestHandler


def initialize_request_handlers(google_max_rpm, traveltime_max_rpm) -> Dict[str, BaseRequestHandler]:
    google_api_key = retrieve_google_api_key()
    credentials = retrieve_traveltime_credentials()
    return {
        GOOGLE_API: GoogleRequestHandler(google_api_key, google_max_rpm),
        TRAVELTIME_API: TravelTimeRequestHandler(credentials.app_id, credentials.api_key, traveltime_max_rpm)
    }
