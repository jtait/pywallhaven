#### v0.2
- added `Wallhaven.get_search_pages()` and `Wallhaven.get_collection_pages()`
    - these methods return generators that iterate through all pages in a response, rather than requiring a specific page as a parameter
- deprecated `Wallhaven.search()` and `Wallhaven.get_collection()` in favour of `Wallhaven.get_search_pages()` and `Wallhaven.get_collection_pages()`
- improved `Wallhaven.util.build_q_string()` to return url-safe escaped strings
- fixed an issue in `Wallhaven.util.build_q_string()` that caused multi-word tags to be handled as separate tags (i.e. a 2 word tag would be treated as 2 tags, etc.)

#### v0.1
- initial release
