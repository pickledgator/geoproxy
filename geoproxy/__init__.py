#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import logging
import tornado.web

from geoproxy.handlers.geoproxy_request import GeoproxyRequestHandler
from geoproxy.third_party_services.google_maps import GoogleMapsServiceHelper
from geoproxy.third_party_services.here import HereServiceHelper


class Geoproxy(tornado.web.Application):
    """Main tornado web application servicing request handlers

    Simple wrapper for tornado.web.Application, packages additional member items such as
    a logger instance and a thread pool executor for coroutines.

    Attributes:
        logger (logging.logger): Logging instance
        executor (ThreadPoolExecutor): Thread pool for coroutines

    """

    def __init__(self, address, port, google_maps_api_key, here_api_app_id, here_api_app_code):
        """Constructor for application

        Args:
            address (string): IP address for the tcp socket to bind to
            port (int): Port for the service to bind to
            google_maps_api_key (string): Google maps geocoder api key
            here_api_app_id (string): Here geocoder app id
            here_api_app_code (string): Here geocoder app code

        """
        self.logger = logging.getLogger("Geoproxy")
        self.executor = ThreadPoolExecutor(max_workers=4)
        available_services = {"google": GoogleMapsServiceHelper(google_maps_api_key),
                              "here": HereServiceHelper(here_api_app_id, here_api_app_code)}
        handlers = [
            # (r"/", IndexHandler, dict()),
            (r"/geocode", GeoproxyRequestHandler, dict(logger=self.logger,
                                                       executor=self.executor,
                                                       available_services=available_services))
        ]
        super(Geoproxy, self).__init__(handlers)
        self.logger.info("Geoproxy listening on {}:{}".format(address, port))
        self.listen(port, address=address)

    def __del__(self):
        """Deconstructor
        """
        self.logger.info("The server is exiting!")
