How to Implement Rate Limiting
==============================

Wallhaven.cc limits requests to 45 per minute. This includes API calls as well as every other request to the host.

Pywallhaven does not include rate limiting by default, but it's simple to implement.

First, create a subclass of :class:`pywallhaven.wallhaven.Wallhaven` and override :py:meth:`pywallhaven.wallhaven.Wallhaven.get_endpoint()`

.. literalinclude:: pywallhaven/rate_limit_example_1.py
    :language: python3

Now, for example, you can use `backoff <https://pypi.org/project/backoff/>`_ to implement a retry strategy:

.. literalinclude:: pywallhaven/rate_limit_example_2.py
    :language: python3

Or if you're running at least Python 3.7, you can use `pyrate-limiter <https://pypi.org/project/pyrate-limiter/>`_, which
will allow rate limiting so you don't exceed the limit in the first place.

.. literalinclude:: pywallhaven/rate_limit_example_3.py
    :language: python3

You can even combine both approaches. This will limit the calls to 45 per-minute, plus use an exponential backoff if the limit is exceeded.

Remember that wallhaven.cc limits all calls, not just API calls, and it seems to do so by IP address.
So if you were running an API downloader and trying to browse the site, you could exceed the limit.

.. literalinclude:: pywallhaven/rate_limit_example_4.py
    :language: python3

Note that none of these examples provide rate limiting that works between multiple processes. So if, for example, you run 2
concurrent processes or even 2 sequential processes that are too close together, it's still possible to exceed the limit.

In that case, `pyrate-limiter <https://pypi.org/project/pyrate-limiter/>`_ has a redis module that may help, or you can
roll your own solution that uses files to store state.
