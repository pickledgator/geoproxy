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

class Response:
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
        handlers = [
           # (r"/", IndexHandler, dict()),
           (r"/geocode", RequestHandler, dict(logger=self.logger, executor=self.executor, \
                google_maps_api_key=google_maps_api_key, here_api_app_id=here_api_app_id, \
                here_api_app_code=here_api_app_code))
        ]
        super(GeoProxy, self).__init__(handlers)
        self.logger.info("GeoProxy listening on {}:{}".format(address, port))

# class MainHandler(tornado.web.RequestHandler):
#     # def initialize(self):

#     def get(self):
#         loader = tornado.template.Loader(".")
#         index_path = run_path("templates/index.html")
#         self.write(loader.load(index_path).generate())

class RequestHandler(tornado.web.RequestHandler):   
    def initialize(self, logger, executor, google_maps_api_key, here_api_app_id, here_api_app_code):
        self.logger = logger
        self.executor = executor
        self.google_maps_api_key = google_maps_api_key
        self.here_api_app_id = here_api_app_id
        self.here_api_app_code = here_api_app_code
        self.set_header("Content-Type", "application/json")

    @coroutine
    def get(self):        
        response = Response()
        address = self.get_arguments("address")
        if len(address) == 0:
            response.set_error("Address parameter is missing from request", "INVALID_REQUEST")
        else:
            sanitized_address_str = self.input_sanitizer(address[0])
            if not sanitized_address_str:
                response.set_error("Address is malformed", "INVALID_REQUEST")
            else:
                google_result = yield self.query_google_maps_api(sanitized_address_str)
                if not google_result[0]:
                    self.logger.warning("Google maps API failed, falling back on HERE API")
                    here_result = yield self.query_here_api(sanitized_address_str)
                    if not here_result[0]:
                        response.set_error("Both geocoding service queries failed", "UNKNOWN_ERROR")
                    else:
                        here_json_response = json.loads(here_result[1])
                        (here_parse_success, lat, lon, query) = self.parse_geo_from_here_response(here_json_response)
                        if here_parse_success:
                            response.set_result("here", lat, lon, query)
                        else:
                            self.logger.error("Failed parsing here API response")
                            response.set_error("Both geocoding service queries failed", "UNKNOWN_ERROR")
                else:
                    google_json_response = json.loads(google_result[1])
                    (google_parse_success, lat, lon, query) = self.parse_geo_from_google_response(google_json_response)
                    if google_parse_success:
                        response.set_result("google", lat, lon, query)
                    else:
                        self.logger.error("Failed parsing google maps API response")
        self.write(response.to_json())
        
    @run_on_executor
    def query_google_maps_api(self, address_str):        
        query = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(address_str, self.google_maps_api_key)
        success = False
        response = None
        try:
            response = urllib.request.urlopen(query, timeout=1).read().decode('utf-8')
            success = True
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            self.logger.error("Error in Google Maps API request: {}".format(error))
            success = False
        except socket.timeout:
            self.logger.info("Timeout in Google Maps API request")
            success = False
        return (success, response)

    @run_on_executor
    def query_here_api(self, address_str):  
        query = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id={}&app_code={}&searchtext={}".format(self.here_api_app_id, self.here_api_app_code, address_str)
        success = False
        response = None
        try:
            response = urllib.request.urlopen(query, timeout=1).read().decode('utf-8')
            success = True
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            self.logger.error("Error in HERE API request: {}".format(error))
            success = False
        except socket.timeout:
            self.logger.info("Timeout in HERE API request")
            success = False
        return (success, response)

    def parse_geo_from_google_response(self, response):
        # always return just the first result, even if there is more than one
        lat = lon = query = None
        success = False
        if response.get('status') == "OK":
            try:
                result = response.get('results')[0]
                query = result.get('formatted_address')
                location = result.get('geometry').get('location')
                lat = location.get('lat')
                lon = location.get('lng')
                success = True
            except Exception as e:
                self.logger.error("Error parsing google maps response: {}".format(e))
        return (success, lat, lon, query)

    def parse_geo_from_here_response(self, response):
        # always return just the first result, even if there is more than one
        lat = lon = query = None
        success = False
        if response.get('Response'):
            try:
                result = response.get('Response').get("View")[0].get('Result')[0]
                location = result.get('Location')
                query = location.get("Address").get("Label")
                lat = location.get("DisplayPosition").get('Latitude')
                lon = location.get("DisplayPosition").get('Longitude')
                success = True
            except Exception as e:
                self.logger.error("Error parsing here response: {}".format(e))
        return (success, lat, lon, query)

    def input_sanitizer(self, address):
        return address.replace(" ", "+")


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