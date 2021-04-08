#### v0.4
- removed rate limiting
    - changed Wallhaven class to allow sub-classes to override get_endpoint(), which will allow more effective rate-limiting of requests
    - removed dependency on urllib3 (except through requests) and [ratelimit](https://pypi.org/project/ratelimit/)
    - see issue [#7](https://github.com/jtait/pywallhaven/issues/7) for more details.
- fixed usage of seed in get_search_pages
- [v0.4 milestone issues](https://github.com/jtait/pywallhaven/milestone/4?closed=1)

#### v0.3
- use the [ratelimit](https://pypi.org/project/ratelimit/) library to limit API requests to 45 per minute, as per [the official docs](https://wallhaven.cc/help/api#limits)
- [v0.3 milestone issues](https://github.com/jtait/pywallhaven/milestone/2?closed=1)

#### v0.2
- added `Wallhaven.get_search_pages()` and `Wallhaven.get_collection_pages()`
    - these methods return generators that iterate through all pages in a response, rather than requiring a specific page as a parameter
- deprecated `Wallhaven.search()` and `Wallhaven.get_collection()` in favour of `Wallhaven.get_search_pages()` and `Wallhaven.get_collection_pages()`
- improved `Wallhaven.util.build_q_string()` to return url-safe escaped strings
- fixed an issue in `Wallhaven.util.build_q_string()` that caused multi-word tags to be handled as separate tags (i.e. a 2 word tag would be treated as 2 tags, etc.)
- [v0.2 milestone issues](https://github.com/jtait/pywallhaven/milestone/1?closed=1)

#### v0.1
- initial release
