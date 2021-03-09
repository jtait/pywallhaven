class RateLimitError(Exception):
    """
    Used by :class:`pywallhaven.wallhaven.Wallhaven`. This is raised when the request response is 429, as per
    https://wallhaven.cc/help/api#limits
    """
    pass
