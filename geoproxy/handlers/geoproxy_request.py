#!/usr/bin/env python

import json
import socket
import time
from tornado.concurrent import run_on_executor
from tornado.gen import coroutine
import tornado.web
import urllib.request
import urllib.error

from geoproxy.api import GeoproxyResponse
from geoproxy.api import GeoproxyRequestParser

class GeoproxyRequestHandler(tornado.web.RequestHandler):   
    def initialize(self, logger, executor, available_services):
        self.logger = logger
        self.executor = executor
        self.set_header("Content-Type", "application/json")
        self.available_services = available_services

    @coroutine
    def get(self):
        start_time = time.time()
        # Create an empty API response
        geo_proxy_response = GeoproxyResponse()
        # Next, parse the inputs from the RESTful query and ensure they are all valid
        geo_proxy_request = GeoproxyRequestParser(self.available_services, geo_proxy_response)
        # if our request parse succeeds, we have valid input data and can proceed
        if geo_proxy_request.parse(self):
            print(type(self))
            self.logger.info("Incoming request:\n{}".format(geo_proxy_request))
            for service in geo_proxy_request.services:
                self.logger.info("Querying third-party service: {}".format(service))
                # Grab the helper object, associated with the service we'd like to request
                service_helper = self.available_services[service]
                service_helper.build_query(geo_proxy_request.address, geo_proxy_request.bounds)
                response_json = yield self.query_third_party_geocoder(service_helper.query)
                if response_json:
                    parse_success = service_helper.parser.parse(response_json)
                    if parse_success == 0:
                        geo_proxy_response.set_error("Zero results", "ZERO_RESULTS")
                    elif not parse_success == None:
                        geo_proxy_response.set_result(service, service_helper.parser.latitude, service_helper.parser.longitude, service_helper.parser.address)
                        break
                   
        self.write(geo_proxy_response.to_json())
        self.logger.info("Response completed in {:0.2f} seconds".format(time.time() - start_time))

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