#!/usr/bin/env python

import json
from geoproxy import Geoproxy
from tornado.testing import AsyncHTTPTestCase
import tornado
import unittest


class TestGeoproxy(AsyncHTTPTestCase):

    def get_app(self):
        return Geoproxy("localhost", 8080, "1", "2", "3")

    def test_no_address(self):
        response = self.fetch('/geocode')
        response_json = json.loads(response.body)
        self.assertEqual(response_json['status'], "INVALID_REQUEST")

    def test_invalid_google_key(self):
        response = self.fetch('/geocode?address=101+North+St&service=google')
        response_json = json.loads(response.body)
        print(response_json)
        self.assertEqual(response_json['status'], "UNKNOWN_ERROR")

    def test_invalid_here_key(self):
        response = self.fetch('/geocode?address=101+North+St&service=here')
        response_json = json.loads(response.body)
        print(response_json)
        self.assertEqual(response_json['status'], "UNKNOWN_ERROR")

    # TODO(pickledgator): Figure out how to unittest third party API requests or mock them
    # without exposing private API keys


if __name__ == '__main__':
    unittest.main()
