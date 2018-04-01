#!/usr/bin/python

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
import socket
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
import tornado.web
import urllib.request

logging.basicConfig(
    format="[%(asctime)s][%(name)s](%(levelname)s) %(message)s", level=logging.DEBUG)

class Coordinate:
    def __init__(self, lat, lon, elev=0):
        self.latitude = lat
        self.longitude = lon
        self.elevation = elev

    def __str__(self):
        return "Lat: {}, Long: {}, Elev: {}".format(self.latitude, self.longitude, self.elevation)

class BoundingBox:
    def __init__(self):
        self.top_left = None
        self.top_right = None
        self.bottom_left = None
        self.bottom_right = None

    def set_bl_tr(self, bl, tr):
        # google format
        self.bottom_left = bl
        self.top_right = tr
        self.top_left = Coordinate(tr.latitude, bl.longitude)
        self.bottom_right = Coordinate(bl.latitude, tr.longitude)

    def set_tl_br(self, tl, br):
        # here format
        self.top_left = tl
        self.bottom_right = br
        self.top_right = Coordinate(tl.latitude, br.longitude)
        self.bottom_left = Coordinate(br.latitude, tl.longitude)

    def __str__(self):
        return "Bounding Box:\n TL: {}\n TR: {}\n BL: {}\n BR: {}".format(self.top_left, self.top_right, self.bottom_left, self.bottom_right)


class ThirdPartyGeocoderHelper:
    def __init__(self, parser):
        self.query = None
        self.parser = parser

    def __str__(self):
        return "ThirdPartyGeocoderHelper:\nQuery: {}".format(self.query)

class GoogleMapsGeocoderHelper(ThirdPartyGeocoderHelper):
    def __init__(self, google_maps_api_key):
        super(GoogleMapsGeocoderHelper, self).__init__(GoogleMapsGeocoderParser())
        self.google_maps_api_key = google_maps_api_key

    def set_query(self, geo_proxy_request):
        self.query = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(geo_proxy_request.address, self.google_maps_api_key)
        if geo_proxy_request.bounds:
            # southwest, northeast
            self.query += "&bounds={},{}|{},{}".format(geo_proxy_request.bounds.bottom_left.latitude, geo_proxy_request.bounds.bottom_left.longitude, geo_proxy_request.bounds.top_right.latitude, geo_proxy_request.bounds.top_right.longitude)

class HereGeocoderHelper(ThirdPartyGeocoderHelper):
    def __init__(self, here_api_app_id, here_api_app_code):
        super(HereGeocoderHelper, self).__init__(HereGeocoderParser())
        self.here_api_app_id = here_api_app_id
        self.here_api_app_code = here_api_app_code

    def set_query(self, geo_proxy_request):
        self.query = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id={}&app_code={}&searchtext={}".format(self.here_api_app_id, self.here_api_app_code, geo_proxy_request.address)
        if geo_proxy_request.bounds:
            # northwest, southeast
            self.query += "&bounds={},{}|{},{}".format(geo_proxy_request.bounds.top_left.latitude, geo_proxy_request.bounds.top_left.longitude, geo_proxy_request.bounds.bottom_right.latitude, geo_proxy_request.bounds.bottom_right.longitude)
        

class ThirdPartyResponseParser:
    def __init__(self):
        self.address_raw = None
        self.address = None
        self.latitude = None
        self.longitude = None
        self.results = 0
        self.response_raw = None
        self.logger = logging.getLogger(__class__.__name__)

class GoogleMapsGeocoderParser(ThirdPartyResponseParser):
    def __init__(self):
        super(GoogleMapsGeocoderParser, self).__init__()

    def parse(self, response):
        self.response_raw = response
        if response.get('status') == "OK":
            try:
                result = response.get('results')[0]
                self.address = result.get('formatted_address')
                location = result.get('geometry').get('location')
                self.latitude = location.get('lat')
                self.longitude = location.get('lng')
                return self
            except Exception as e:
                self.logger.error("Error parsing response: {}".format(e))
        return None

class HereGeocoderParser(ThirdPartyResponseParser):
    def __init__(self):
        super(HereGeocoderParser, self).__init__()

    def parse(self, response):
        self.response_raw = response
        if response.get('Response'):
            try:
                result = response.get('Response').get("View")[0].get('Result')[0]
                location = result.get('Location')
                self.address = location.get("Address").get("Label")
                self.latitude = location.get("DisplayPosition").get('Latitude')
                self.longitude = location.get("DisplayPosition").get('Longitude')
                return self
            except Exception as e:
                self.logger.error("Error parsing response: {}".format(e))
        return None

class GeoProxyRequestParser:
    def __init__(self, available_services, geo_proxy_response):
        self.logger = logging.getLogger(__class__.__name__)
        self.address = None
        self.services = []
        self.available_services = available_services
        self.bounds = None
        self.geo_proxy_response = geo_proxy_response

    def __str__(self):
        return "Address: {}\nServices: {}\nBounds: {}".format(self.address, self.services, self.bounds)

    def parse_bounding_coordinates(self, bounds_string):
        corners = bounds_string.split("|")
        if len(corners) != 2:
            return None
        coordinates = []
        for corner in corners:
            corner_coords = corner.split(",")
            if len(corner_coords) != 2:
                return None
            for coord in corner_coords:
                coordinates.append(float(coord))
        if len(coordinates) == 4:
            return coordinates
        else:
            return None

    def find_missing_elements(self, full_list, partial_list):
        return set(full_list) - set(partial_list)

    def parse(self, request):
        # required field
        address = request.get_arguments("address")
        if len(address) == 1:
            # verify that the address field is not empty
            if address[0] == "":
                self.logger.error("Address is invalid")
                self.geo_proxy_response.set_error("Address is invalid", "INVALID_REQUEST")
                return False
            # clean up the address string to replace invalid characters
            self.address = address[0].replace(" ", "+")
        else:
            self.logger.error("A single address parameter is required within the request")
            self.geo_proxy_response.set_error("A single address parameter is required within the request", "INVALID_REQUEST")
            return False

        # optional fields
        service = request.get_arguments("service")
        if len(service) == 1 and service[0] in self.available_services:
                # add the desired primary service to our ordered list
                self.services.append(service[0])
                # backfill additional services from the available services as fallback options after the primary
                [self.services.append(s) for s in self.find_missing_elements(self.available_services.keys(), self.services)]
        else:
            # if un-specified, just default the ordered services to the available services
            [self.services.append(s) for s in self.available_services.keys()]

        bounds = request.get_arguments("bounds")
        if len(bounds) == 1:
            coordinates = self.parse_bounding_coordinates(bounds[0])
            if coordinates:
                self.bounds = BoundingBox()
                # TODO(pickledgator): Are the 3rd party geocoders robust to sending the wrong corners?
                if self.services[0] == "google":
                    # assume that if the service is not specified or its google, that the bounding box
                    # coordinates are provided in google's format
                    self.bounds.set_bl_tr(Coordinate(coordinates[0], coordinates[1]), Coordinate(coordinates[2], coordinates[3]))
                elif self.services[0] == "here":
                    # otherwise, if the service is specified as here, assume the bounding box
                    # coordinates are provided in here's format
                    self.bounds.set_tl_br(Coordinate(coordinates[0], coordinates[1]), Coordinate(coordinates[2], coordinates[3]))
                else:
                    self.logger.warning("Error identifying format of bounding box coordinates from service: {}".format(self.services[0]))
            else:
                self.logger.warning("Error parsing bounding box coordinates")
        return True


class GeoProxyResponse:
    """Help package an API response

    Valid status messages:
    "OK"
    "ZERO_RESULTS"
    "INVALID_REQUEST"
    "UNKNOWN_ERROR"

    """
    def __init__(self):
        self.query = None
        self.error = None
        self.status = None
        self.result = None

    def set_error(self, message, status_type):
        self.error = message
        self.status = status_type

    def set_result(self, source, lat, lon, query):
        self.query = query
        self.result = {'source': source, 'lat': lat, 'lon': lon}
        self.status = "OK"

    def to_json(self):
        d = dict()
        if self.error:
            d['error'] = self.error
            d['status'] = self.status
        else:
            d['query'] = self.query
            d['status'] = self.status
            d['result'] = self.result

        return json.dumps(d)

class GeoProxy(tornado.web.Application):
    def __init__(self, address, port, google_maps_api_key, here_api_app_id, here_api_app_code):
        self.logger = logging.getLogger("GeoProxy")
        self.executor = ThreadPoolExecutor(max_workers=4)
        available_services = { "google": GoogleMapsGeocoderHelper(google_maps_api_key), 
                                    "here": HereGeocoderHelper(here_api_app_id, here_api_app_code) }
        handlers = [
           # (r"/", IndexHandler, dict()),
           (r"/geocode", RequestHandler, dict(logger=self.logger, executor=self.executor, available_services=available_services))
        ]
        super(GeoProxy, self).__init__(handlers)
        self.logger.info("GeoProxy listening on {}:{}".format(address, port))

class RequestHandler(tornado.web.RequestHandler):   
    def initialize(self, logger, executor, available_services):
        self.logger = logger
        self.executor = executor
        self.set_header("Content-Type", "application/json")
        self.available_services = available_services

    @coroutine
    def get(self):        
        # Create an empty API response
        geo_proxy_response = GeoProxyResponse()
        # Next, parse the inputs from the RESTful query and ensure they are all valid
        geo_proxy_request = GeoProxyRequestParser(self.available_services, geo_proxy_response)
        # if our request parse succeeds, we have valid input data and can proceed
        if geo_proxy_request.parse(self):
            for service in geo_proxy_request.services:
                # Grab the helper object, associated with the service we'd like to request
                service_helper = self.available_services[service]
                service_helper.set_query(geo_proxy_request)
                response_json = yield self.query_third_party_geocoder(service_helper.query)
                if response_json:
                    parse_success = service_helper.parser.parse(response_json)
                    if parse_success:
                        geo_proxy_response.set_result(service, service_helper.parser.latitude, service_helper.parser.longitude, service_helper.parser.address)
                        break
                   
        self.write(geo_proxy_response.to_json())

    @run_on_executor
    def query_third_party_geocoder(self, query, timeout=1):      
        response = None
        try:
            response = urllib.request.urlopen(query, timeout=timeout).read().decode('utf-8')
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            self.logger.error("Error in API request: {}".format(error))
        except socket.timeout:
            self.logger.info("Timeout in API request")
        # if our response succeeds, then parse it and pass the parser back upstream
        if response:
            response_json = json.loads(response)
            # if the parser suceeds, it'll pass a ref to itself back upstream, otherwise None
            return response_json
        # API query failed
        else:
            return None


if __name__ == "__main__":
    
    # Parse arguments from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", default="localhost", help="IP address where the service is running (default: localhost)")
    parser.add_argument("-p", "--port", default=8080, help="Port that the service runs on (default: 8080)")
    args = parser.parse_args()

    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    here_api_app_id = os.environ.get('HERE_API_APP_ID')
    here_api_app_code = os.environ.get('HERE_API_APP_CODE')
    
    # Create server object and set it up to listen on the desired port
    geo_proxy = GeoProxy(args.address, args.port, google_maps_api_key, here_api_app_id, here_api_app_code)
    geo_proxy.listen(args.port, args.address)
    
    try:
        # start the ioloop
        IOLoop.instance().start()
    except KeyboardInterrupt:
        # ensure that the event loop stops cleanly on interrupt
        geo_proxy.logger.info("The server is exiting!")
        IOLoop.instance().stop()