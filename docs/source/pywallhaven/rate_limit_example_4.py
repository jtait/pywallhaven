import backoff
from pyrate_limiter import Limiter, RequestRate, Duration, MemoryListBucket

from pywallhaven import Wallhaven
from pywallhaven.exceptions import RateLimitError

rate = RequestRate(45, Duration.MINUTE)

limiter = Limiter(rate, bucket_class=MemoryListBucket)

# since the above limiter is global, it can be reused in other calls such as a request to download a specific wallpaper


class LimitedWallhaven(Wallhaven):

    @backoff.on_exception(backoff.expo, RateLimitError)
    @limiter.ratelimit('endpoint', delay=True)
    def get_endpoint(self, url) -> dict:
        """
        overrides Wallhaven.get_endpoint()

        Rate limited by limiter defined outside class to 45 calls per minute
        Also implements a backoff in case other processes make calls to wallhaven.cc
        """
        return super().get_endpoint(url)
