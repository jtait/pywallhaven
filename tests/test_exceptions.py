"""
Unit tests for pywallhaven.exceptions
"""


import unittest

import responses

from pywallhaven.exceptions import RateLimitError
from pywallhaven import Wallhaven


class TestAPILimitError(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(RateLimitError):
            raise RateLimitError


class TestMockEndpoint(unittest.TestCase):
    def setUp(self):
        """
        Helps cleanup responses after test runs to ensure clean state.
        :return:
        """
        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    @responses.activate
    def test_error_code_response(self):
        w = Wallhaven()
        responses.add(responses.GET, 'https://wallhaven.cc/api/v1/search', status=429)
        with self.assertRaises(RateLimitError):
            w.search()
