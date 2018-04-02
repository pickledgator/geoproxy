#!/usr/bin/env python

import json
from geoproxy.api import GeoproxyRequestParser
from geoproxy.api import GeoproxyResponse
import unittest


class MockRequestHandler:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def get_arguments(self, key):
        try:
            return self.dictionary[key]
        except Exception as e:
            return []


class TestAPI(unittest.TestCase):

    def test_request_parser_constructor(self):
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        self.assertEqual(len(req_parser.services), 0)
        self.assertEqual(req_parser.available_services, mock_services)
        self.assertEqual(req_parser.geo_proxy_response, response)

    def test_parse_bounding_coordinates(self):
        req_parser = GeoproxyRequestParser(None, None)
        # way wrong
        self.assertIsNone(req_parser.parse_bounding_coordinates("Bad"))
        # not enough coords
        self.assertIsNone(req_parser.parse_bounding_coordinates("1.0,2.0"))
        # too many coords
        self.assertIsNone(req_parser.parse_bounding_coordinates("1.0,2.0|1.0,2.0|1.0,2.0"))
        # wrong delim
        self.assertIsNone(req_parser.parse_bounding_coordinates("1.0,2.0;1.0,2.0"))
        # wrong num lat/long
        self.assertIsNone(req_parser.parse_bounding_coordinates("1.0,2.0,3.0|1.0,2.0"))
        # right
        out = req_parser.parse_bounding_coordinates("1.0,2.0|3.0,4.0")
        self.assertIsNotNone(out)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[1], 2.0)

    def test_missing_elements(self):
        req_parser = GeoproxyRequestParser(None, None)
        out = req_parser.find_missing_elements([1, 2, 3], [2])
        self.assertEqual(out, [1, 3])
        out = req_parser.find_missing_elements([1, 2, 3], [1, 2, 3])
        self.assertEqual(out, [])
        out = req_parser.find_missing_elements([1, 2, 3], [1, 2, 3, 4])
        self.assertEqual(out, [])

    def test_google_parse(self):
        valid = {"address": ["Addr"], "service": ["google"], "bounds": ["1.0,2.0|3.0,4.0"]}
        mock_handler = MockRequestHandler(valid)
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        out = req_parser.parse(mock_handler)
        self.assertTrue(out)
        self.assertEqual(req_parser.address, "Addr")
        self.assertEqual(req_parser.services, ["google", "here"])
        self.assertEqual(req_parser.bounds.bottom_left.latitude, 1.0)

    def test_here_parse(self):
        valid = {"address": ["Addr"], "service": ["here"], "bounds": ["1.0,2.0|3.0,4.0"]}
        mock_handler = MockRequestHandler(valid)
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        out = req_parser.parse(mock_handler)
        self.assertTrue(out)
        self.assertEqual(req_parser.address, "Addr")
        self.assertEqual(req_parser.services, ["here", "google"])
        self.assertEqual(req_parser.bounds.top_left.latitude, 1.0)

    def test_bad_parse(self):
        invalid = {"service": ["google"], "bounds": ["1.0,2.0|3.0,4.0"]}
        mock_handler = MockRequestHandler(invalid)
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        out = req_parser.parse(mock_handler)
        # missing address
        self.assertFalse(out)
        self.assertEqual(response.status, "INVALID_REQUEST")

    def test_bad_parse2(self):
        invalid = {"address": ["Addr"], "service": ["blah"], "bounds": ["1.0,2.0|3.0,4.0"]}
        mock_handler = MockRequestHandler(invalid)
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        out = req_parser.parse(mock_handler)
        self.assertTrue(out)
        # invalid primary service
        self.assertEqual(req_parser.services, ["google", "here"])
        self.assertEqual(response.query, "Addr")

    def test_bad_parse3(self):
        invalid = {"address": ["Addr", "Addr2"], "service": ["blah"], "bounds": ["1.0,2.0|3.0,4.0"]}
        mock_handler = MockRequestHandler(invalid)
        response = GeoproxyResponse()
        mock_services = {"google": None, "here": None}
        req_parser = GeoproxyRequestParser(mock_services, response)
        out = req_parser.parse(mock_handler)
        # too many addresses
        self.assertFalse(out)
        self.assertEqual(response.status, "INVALID_REQUEST")

    def test_response(self):
        gp = GeoproxyResponse()
        self.assertIsNone(gp.query)
        self.assertIsNone(gp.error)
        self.assertIsNone(gp.result)
        gp.set_error("message", "TYPE")
        self.assertEqual(gp.error, "message")
        self.assertEqual(gp.status, "TYPE")
        self.assertIsNone(gp.result)
        self.assertEqual(len(json.loads(gp.to_json()).keys()), 2)
        gp2 = GeoproxyResponse()
        gp2.set_result("google", 1.0, 2.0, "Addr string")
        self.assertEqual(gp2.resolved_address, "Addr string")
        self.assertEqual(type(gp2.result), dict)
        self.assertEqual(gp2.result['source'], "google")
        self.assertEqual(gp2.status, "OK")
        self.assertIsNone(gp2.error)
        self.assertEqual(len(json.loads(gp2.to_json()).keys()), 4)
        self.assertEqual(type(gp2.to_json()), str)


if __name__ == '__main__':
    unittest.main()
