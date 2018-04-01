#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import logging
import tornado.web

from geoproxy.handlers.geoproxy_request import GeoproxyRequestHandler
from geoproxy.third_party_services.google_maps import GoogleMapsServiceHelper
from geoproxy.third_party_services.here import HereServiceHelper


class Geoproxy(tornado.web.Application):

    def __init__(self, address, port, google_maps_api_key, here_api_app_id, here_api_app_code):
        self.logger = logging.getLogger("Geoproxy")
        self.executor = ThreadPoolExecutor(max_workers=4)
        available_services = {"google": GoogleMapsServiceHelper(google_maps_api_key),
                              "here": HereServiceHelper(here_api_app_id, here_api_app_code)}
        handlers = [
            # (r"/", IndexHandler, dict()),
            (r"/geocode", GeoproxyRequestHandler, dict(logger=self.logger,
                                                       executor=self.executor, available_services=available_services))
        ]
        super(Geoproxy, self).__init__(handlers)
        self.logger.info("Geoproxy listening on {}:{}".format(address, port))

    def __del__(self):
        self.logger.info("The server is exiting!")
