#!/usr/bin/env python

import logging

"""Base classes for third party services

Since each third party query structure and parser will be different, child classes should
be implemented on top of these base classes.

"""


class ThirdPartyServiceHelper(object):
    """A container that has both a valid query string and a parser

    Attributes:
        query (string): Valid query string to be sent to the third party service
        parser (ThirdPartyServiceResponseParser): Parser associated with third party service

    """
    def __init__(self, parser):
        self.query = None
        self.parser = parser

    def build_query(self):
        """Virtual method for build_query
        """
        pass

    def __str__(self):
        return "ThirdPartyGeocoderHelper:\nQuery: {}".format(self.query)


class ThirdPartyServiceResponseParser(object):
    """A base class parser for a specified third party service

    The members of this class should be populated within a method called parse(), if the
    data is valid, otherwise members should be left as None.

    Attributes:
        address_raw (string): Raw query string that was sent to the third party service
        address (string): Parsed address from the third party service response
        latitude (float): Parsed latitude from the third party service response
        longitude (float): Parsed longitude from the third party service response
        results (string): Number of results from the third party service response
        response_raw (string): Complete response from the third party service response (for debug)
        logger (logging.logger): Logger instance

    """
    def __init__(self):
        self.address_raw = None
        self.address = None
        self.latitude = None
        self.longitude = None
        self.results = 0
        self.response_raw = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self):
        """Virtual method for parse
        """
        pass
