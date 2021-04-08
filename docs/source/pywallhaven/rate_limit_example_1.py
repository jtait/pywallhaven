from pywallhaven import Wallhaven


class LimitedWallhaven(Wallhaven):
    """
    This class will override get_endpoint to apply rate limiting
    """

    def get_endpoint(self, url) -> dict:
        """
        overrides Wallhaven.get_endpoint()

        Apply your rate limiting on this method, through wrappers or intermediary steps.
        """
        return super().get_endpoint(url)
