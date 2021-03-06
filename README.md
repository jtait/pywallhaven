# pywallhaven
Python API for wallhaven.cc

This is an implementation of the [API](https://wallhaven.cc/help/api) for [wallhaven.cc](https://wallhaven.cc/). It provides a simple interface to access the data provided by the API to enable development of tools/programs.

#### Documentation
Documentation is available at [pywallhaven.readthedocs.io](https://pywallhaven.readthedocs.io/en/latest/).

#### Disclaimer
This project and its author has no affiliation with [wallhaven.cc](https://wallhaven.cc/), and as such this project should be considered "unofficial". Use of wallhaven.cc is subject to their [Terms of Service](https://wallhaven.cc/terms) and [Privacy Policy](https://wallhaven.cc/privacy-policy).

Compatibility with the wallhaven.cc API is done on a best-effort basis, but changes to the API may not be immediately accounted for in this library. Any compatibilty issues should be raised in the project's [issue tracker](https://github.com/jtait/pywallhaven/issues).

#### Wallhaven Issues
Some issues are caused by problems with [wallhaven.cc](https://wallhaven.cc/), not _pywallhaven_. The known issues that affect API usage are tracked with the "wallhaven issue" label.

[View the List](https://github.com/jtait/pywallhaven/labels/wallhaven%20issue)

#### Notes
- Wallhaven limits all requests to 45 per minute, not just API calls. This means that if you use this library to make API calls and then implement other functionality that makes requests to the site (e.g. to download an image), those requests are included in the limit.

#### Dependencies
This project uses these libraries:
- [requests](https://pypi.org/project/requests/)
- [dataclasses](https://pypi.org/project/dataclasses/) (for Python 3.6)
- [responses](https://pypi.org/project/responses/) (for testing only)

#### Links
- wallhaven.cc (https://wallhaven.cc/)
- official API reference (https://wallhaven.cc/help/api)
- issue tracker (https://github.com/jtait/pywallhaven/issues)
- documentation (https://pywallhaven.readthedocs.io/en/latest/)
