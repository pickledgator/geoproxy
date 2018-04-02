#!/usr/bin/env python

import logging


class ThirdPartyServiceHelper(object):
    def __init__(self, parser):
        self.query = None
        self.parser = parser

    def __str__(self):
        return "ThirdPartyGeocoderHelper:\nQuery: {}".format(self.query)


class ThirdPartyServiceResponseParser(object):
    def __init__(self):
        self.address_raw = None
        self.address = None
        self.latitude = None
        self.longitude = None
        self.results = 0
        self.response_raw = None
        self.logger = logging.getLogger(self.__class__.__name__)
