import backoff

from pywallhaven import Wallhaven
from pywallhaven.exceptions import RateLimitError


class LimitedWallhaven(Wallhaven):

    @backoff.on_exception(backoff.expo, (RateLimitError), max_tries=10)
    def get_endpoint(self, url) -> dict:
        """
        overrides Wallhaven.get_endpoint()

        Wrapped in backoff.on_exception - will use exponential backoff to retry up to 10 times
        """
        return super().get_endpoint(url)
