#!/usr/bin/env python

from geoproxy.geometry import BoundingBox
from geoproxy.geometry import Coordinate
from geoproxy.third_party_services.google_maps import GoogleMapsServiceHelper
from geoproxy.third_party_services.google_maps import GoogleMapsServiceResponseParser
from geoproxy.third_party_services.here import HereServiceHelper
from geoproxy.third_party_services.here import HereServiceResponseParser
from geoproxy.third_party_services.service_base import ThirdPartyServiceHelper
from geoproxy.third_party_services.service_base import ThirdPartyServiceResponseParser
from geoproxy.api import GeoproxyRequestParser
import json
import unittest


class TestThirdPartyServices(unittest.TestCase):
    def test_service_helper(self):
        parser = ThirdPartyServiceResponseParser()
        a = ThirdPartyServiceHelper(parser)
        self.assertEqual(a.parser, parser)
        self.assertIsNone(a.query)

    def test_service_response_parser(self):
        a = ThirdPartyServiceResponseParser()
        self.assertIsNotNone(a.logger)
        self.assertIsNone(a.address)


class TestGoogleServices(unittest.TestCase):
    def test_google_maps_service_helper(self):
        gmsh = GoogleMapsServiceHelper("key")
        self.assertIsNone(gmsh.query)
        self.assertEqual(type(gmsh.parser), GoogleMapsServiceResponseParser)
        gmsh.build_query("query", None)
        self.assertEqual(
            gmsh.query, "https://maps.googleapis.com/maps/api/geocode/json?address=query&key=key")
        bb = BoundingBox()
        coord1 = Coordinate("1.0", "0.0")
        coord2 = Coordinate("0.0", "1.0")
        bb = BoundingBox()
        bb.set_bl_tr(coord1, coord2)
        gmsh.build_query("two+words", bb)
        string = "https://maps.googleapis.com/maps/api/geocode/json?address=two+words" \
            "&key=key&bounds=1.0,0.0|0.0,1.0"
        self.assertEqual(gmsh.query, string)

    def test_google_maps_response_parser_valid(self):
        gmsrp = GoogleMapsServiceResponseParser()
        fake_response = {"status": "OK", "results": [
            {"formatted_address": "Addr", "geometry": {"location": {"lat": "1.0", "lng": "2.0"}}}]}
        out = gmsrp.parse(fake_response)
        self.assertIsNotNone(out)
        self.assertEqual(out.address, "Addr")
        self.assertEqual(out.latitude, 1.0)
        self.assertEqual(out.longitude, 2.0)

    def test_google_maps_response_parser_no_results(self):
        gmsrp = GoogleMapsServiceResponseParser()
        fake_response = {"status": "ZERO_RESULTS", "results": []}
        out = gmsrp.parse(fake_response)
        self.assertIsNotNone(out)
        self.assertEqual(out, 0)

    def test_google_maps_response_parser_invalid(self):
        gmsrp = GoogleMapsServiceResponseParser()
        # location dict is invalid (missing lat, lng)
        fake_response = {"status": "OK", "results": [
            {"formatted_address": "Addr", "geometry": {"location": 1}}]}
        out = gmsrp.parse(fake_response)
        self.assertIsNone(out)


class TestHereServices(unittest.TestCase):
    def test_here_service_helper(self):
        hsh = HereServiceHelper("appid", "appcode")
        self.assertIsNone(hsh.query)
        self.assertEqual(type(hsh.parser), HereServiceResponseParser)
        hsh.build_query("query", None)
        string = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id=appid" \
            "&app_code=appcode&searchtext=query"
        self.assertEqual(hsh.query, string)
        bb = BoundingBox()
        coord1 = Coordinate("0.0", "0.0")
        coord2 = Coordinate("1.0", "1.0")
        bb = BoundingBox()
        bb.set_tl_br(coord1, coord2)
        hsh.build_query("two+words", bb)
        string = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id=appid" \
            "&app_code=appcode&searchtext=two+words&bbox=0.0,0.0;1.0,1.0"
        self.assertEqual(hsh.query, string)

    def test_here_response_parser_valid(self):
        hsrp = HereServiceResponseParser()
        fake_response = {"Response": {"View": [{"Result": [{"Location": {"Address": {
            "Label": "Addr"}, "DisplayPosition": {"Latitude": 1.0, "Longitude": 2.0}}}]}]}}
        out = hsrp.parse(fake_response)
        self.assertIsNotNone(out)
        self.assertEqual(out.address, "Addr")
        self.assertEqual(out.latitude, 1.0)
        self.assertEqual(out.longitude, 2.0)

    def test_here_response_parser_no_results(self):
        hsrp = HereServiceResponseParser()
        fake_response = {"Response": {"View": []}}
        out = hsrp.parse(fake_response)
        self.assertIsNotNone(out)
        self.assertEqual(out, 0)

    def test_here_response_parser_invalid(self):
        hsrp = HereServiceResponseParser()
        # Display_Position != DisplayPosition
        fake_response = {"Response": {"View": [{"Result": [{"Location": {"Address": {
            "Label": "Addr"}, "Display_Position": {"Latitude": 1.0, "Longitude": 2.0}}}]}]}}
        out = hsrp.parse(fake_response)
        self.assertIsNone(out)


if __name__ == '__main__':
    unittest.main()
