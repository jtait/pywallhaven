# pywallhaven
Python API for wallhaven.cc

This is an implementation of the [API](https://wallhaven.cc/help/api) for [wallhaven.cc](https://wallhaven.cc/). It provides a simple interface to access the data provided by the API to enable development of tools/programs.

#### Disclaimer
This project and its author has no affiliation with [wallhaven.cc](https://wallhaven.cc/), and as such this project should be considered "unofficial". Use of wallhaven.cc is subject to their [Terms of Service](https://wallhaven.cc/terms) and [Privacy Policy](https://wallhaven.cc/privacy-policy).

Compatibility with the wallhaven.cc API is done on a best-effort basis, but changes to the API may not be immediately accounted for in this library. Any compatibilty issues should be raised in the project's issue tracker.

#### Known Issues
- Seeds: The seed parameter doesn't work for random searches. It is passed through to the API call, but it appears that the API ignores the given seed. The seed that is returned in the Meta object is random, and therefore cannot be used over multiple pages of random search.

#### Dependencies
This project uses these libraries:
- [requests](https://pypi.org/project/requests/)
- [urllib3](https://pypi.org/project/urllib3/)
- [dataclasses](https://pypi.org/project/dataclasses/)
- [responses](https://pypi.org/project/responses/) (for testing only)

#### Links
- wallhaven.cc (https://wallhaven.cc/)
- official API reference (https://wallhaven.cc/help/api)
