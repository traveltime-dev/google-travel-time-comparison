from abc import ABC, abstractmethod
from datetime import datetime

from aiolimiter import AsyncLimiter
from traveltimepy import Coordinates

from google_travel_time_comparison.config import Mode


class BaseRequestHandler(ABC):
    _rate_limiter: AsyncLimiter
    _just_checking_if_it_complains: str

    @abstractmethod
    async def send_request(self,
                           origin: Coordinates,
                           destination: Coordinates,
                           departure_time: datetime,
                           mode: Mode):
        pass

    @property
    def rate_limiter(self) -> AsyncLimiter:
        return self._rate_limiter
