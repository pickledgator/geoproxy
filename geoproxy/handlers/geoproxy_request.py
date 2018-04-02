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
    """Tornado handler class associated with geocode requests

    This class is responsible for handling requests made to "/geocode". It's responsibilies
    include parsing the incoming request data, querying the appropriate third party geocoding
    services, parsing response messages from those third party services, packaging a response
    back to the geoproxy client and handling errors conditions.

    The handler utilizes an asynchronous get coroutine that tasks the third party service query
    on a thread pool executor to allow the tornado server to simultaneously serve other connections
    without blocking on slow third party service responses.

    The class inherits from a tranditional tornado.web.RequestHandler and overwrites initialize()
    and get().

    Attributes:
        logger (logging.logger): Logger instances
        executor (ThreadPoolExecutor): Thread pool for async tasks
        available_services (dict): Map from service name to ThirdPartyServiceHelper

    """

    def initialize(self, logger, executor, available_services):
        """Constructor for GeoproxyRequestHandler

        Args:
            logger (logging.logger): Logger instances
            executor (ThreadPoolExecutor): Thread pool for async tasks
            available_services (dict): Map from service name to ThirdPartyServiceHelper

        """
        self.logger = logger
        self.executor = executor
        self.set_header("Content-Type", "application/json")
        self.available_services = available_services

    @coroutine
    def get(self):
        """Request handler for method=GET

        Responsible for spawning third party geocoder query tasks based on parsed request data

        Pseudo code:
        - Create empty response
        - Parse incoming request
        - If parse success:
            - For each third party service:
                - Build third party service query from incoming request data
                - Spawn query task and wait on future for third party response
                - Parse third party response
                - If success:
                    - Set response result
                    - Break
                - Next service in loop
        - Else:
            - Set response error
        - Send response

        """
        start_time = time.time()
        # Create an empty API response
        geo_proxy_response = GeoproxyResponse()

        try:
            # Next, parse the inputs from the RESTful query and ensure they are all valid
            geo_proxy_request = GeoproxyRequestParser(self.available_services, geo_proxy_response)
            # if our request parse succeeds, we have valid input data and can proceed
            if geo_proxy_request.parse(self):
                self.logger.info("Incoming request:\n{}".format(geo_proxy_request))
                # iterate through each service in request.services until we get a successful result
                for service in geo_proxy_request.services:
                    self.logger.info("Querying third-party service: {}".format(service))
                    # Grab the third party helper object, associated with the service
                    # The helper assists with third party query construction and parsing
                    service_helper = self.available_services[service]
                    # build the third party query based on our request inputs
                    service_helper.build_query(geo_proxy_request.address, geo_proxy_request.bounds)
                    # run the query and yield the response
                    response_json = yield self.query_third_party_geocoder(service_helper.query)
                    if response_json:
                        # if we got a valid response from the third party query, parse it!
                        parse_success = service_helper.parser.parse(response_json)
                        # fragile detection if there was a valid response, but zero results
                        if parse_success == 0:
                            geo_proxy_response.set_error("Zero results", "ZERO_RESULTS")
                        # otherwise assume the parse was successful, and we extracted data
                        # package it into our response object to be sent out.
                        elif parse_success is not None:
                            geo_proxy_response.error = None
                            geo_proxy_response.set_result(
                                service, service_helper.parser.latitude,
                                service_helper.parser.longitude,
                                service_helper.parser.address)
                            # if we get a valid result, don't keep querying the other third
                            # party services
                            # NOTE: Making an assumption that we are only returning results from the
                            # first valid third party service
                            break

            # if we had an error with both service requests, but no error has been set, do it now
            # this handles cases like wrong API keys, offline services, etc.
            if not geo_proxy_response.status == "OK" and geo_proxy_response.error is None:
                geo_proxy_response.set_error("Error in third-party API requests", "UNKNOWN_ERROR")

        except Exception as e:
            geo_proxy_response.set_error(
                "Caught general exception in server: {}".format(e), "UNKNOWN_ERROR")

        # Ensure that a response is always sent so the socket doesn't bind
        self.write(geo_proxy_response.to_json())
        self.logger.info("Response completed in {:0.2f} seconds".format(time.time() - start_time))

    @run_on_executor
    def query_third_party_geocoder(self, query, timeout=1):
        """Sends HTTP request to third party geocoding service

        Args:
            query (string): Query string to third party API including API keys
            timeout (int): Number of seconds to wait for response before handling timeout exception

        Returns:
            None/dict: JSON data as dict on query success, otherwise None

        """
        response = None
        # TODO(pickledagator): Consider bubbling up exceptions here
        try:
            response = urllib.request.urlopen(query, timeout=timeout).read().decode('utf-8')
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            self.logger.error("Error in API request: {}".format(error))
        except socket.timeout:
            self.logger.info("Timeout in API request")
        # if our response succeeds, pass the data back upstream for the parsers to use
        if response:
            response_json = json.loads(response)
            # deserialized the data before it goes out so that can use it easily
            return response_json
        # third party API query failed
        else:
            return None
