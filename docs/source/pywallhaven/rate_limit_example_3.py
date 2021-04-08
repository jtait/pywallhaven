from pyrate_limiter import Limiter, RequestRate, Duration, MemoryListBucket

from pywallhaven import Wallhaven

rate = RequestRate(45, Duration.MINUTE)

limiter = Limiter(rate, bucket_class=MemoryListBucket)

# since the above limiter is global, it can be reused in other calls such as a request to download a specific wallpaper


class LimitedWallhaven(Wallhaven):

    @limiter.ratelimit('endpoint', delay=True)
    def get_endpoint(self, url) -> dict:
        """
        overrides Wallhaven.get_endpoint()

        rate limited by limiter defined outside class to 45 calls per minute
        """
        return super().get_endpoint(url)
