#!/usr/bin/env python

import json
import logging

from geoproxy.geometry import BoundingBox
from geoproxy.geometry import Coordinate


class GeoproxyRequestParser:
    """Assisting methods for parsing a RESTful request to the API

    Provides a series of methods for parsing an incoming geoproxy request from tornado.
    The parse method checks for input data validity of both the required address field
    and the optional service and bounds fields. After a successful parse, the class's
    member variables are populated.

    Attributes:
        logger (logging.logger): Logger instance
        address (string): Address string from the request, populated by parse()
        services ([string]): Services list in order of priority, populated by parse()
        available_services (dict): Full list of available services, used to populate
            extra backup services if primary fails
        bounds (BoundingBox): Optional bounding box coordinates to use in the query
        geo_proxy_response (GeoproxyResponse): Reference to the geoproxy API response

    """

    def __init__(self, available_services, geo_proxy_response):
        """Constructor for the request parser

        Args:
            available_services (dict): Maps from service name to ThirdPartyServiceHelper
            geo_proxy_response (GeoproxyResponse): Reference to the geoproxy API response

        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.address = None
        self.services = []
        self.available_services = available_services
        self.bounds = None
        self.geo_proxy_response = geo_proxy_response

    def __str__(self):
        """Human readable representation of the request parser
        """
        return "Address: {}\nServices: {}\nBounds: {}".format(
            self.address, self.services, self.bounds)

    def parse_bounding_coordinates(self, bounds_string):
        """Extracts coordinates (floats) from a bounds string

        The representation of coordinates 1 and 2 after parsing is agnostic in the
        context of this helper, it just parses a string into floats.

        Args:
            bounds_string (string): Input from http request to be parsed

        Returns:
            [floats]: List of 4 floats representing coord1.lat, coord1.long,
                      coord2.lat, coord2.long.

        """
        corners = bounds_string.split("|")
        if len(corners) != 2:
            # TODO(pickledgator): Consider bubbling up exceptions here instead
            return None
        coordinates = []
        for corner in corners:
            corner_coords = corner.split(",")
            if len(corner_coords) != 2:
                # TODO(pickledgator): Consider bubbling up exceptions here instead
                return None
            for coord in corner_coords:
                coordinates.append(float(coord))
        if len(coordinates) == 4:
            return coordinates
        else:
            # TODO(pickledgator): Consider bubbling up exceptions here instead
            return None

    def find_missing_elements(self, full_list, partial_list):
        """Compares two lists and finds the differences

        Args:
            full_list [obj]: Complete list
            partial_list [obj]: Partial list to compare against complete list

        Returns:
            [obj]: List of objs that are in complete list but not partial list

        """
        return list(set(full_list) - set(partial_list))

    def parse(self, request):
        """Parses a tornado HTTP request and populates the class's members variables

        The parser assumes that there is one required argument in the request (address)
        and two optional arguments (service, bounds). If the address argument is provided,
        it checks for validity and attempts to sanitize the string.

        If the service argument is provided, it checks to see if the service is within the
        available services. If the specified request service is valid, it sets this service
        as the primary service for the request. All remaining available services are then backfilled
        into the class's service list as fallback options if the primary service fails. If the
        service argument is omitted, all available services are used (based on dict ordering).
        Eg:
        available_services = ["1", "2"]
        request.service = "2"
        self.services = ["2", "1"]

        If the bounds argument is provided, it attempts to parse the string using the class helper
        function. Upon successful bounds string parsing, the 2 extracted coordinates are then used
        to create a bounding box object. It is assumed that the geoproxy API expects the bounds to
        be formatted as bottom_left.lat,bottom_left.lon|top_right.lat,top_right.lon.

        Args:
            request (tornado.web.RequestHandler): Object containing the request data

        Returns:
            bool: If the parse is successful or not

        """
        # required field
        address = request.get_arguments("address")
        if len(address) == 1:
            # verify that the address field is not empty
            if address[0] == "":
                self.logger.error("Address is invalid")
                self.geo_proxy_response.set_error("Address is invalid", "INVALID_REQUEST")
                # TODO(pickledgator): Consider bubbling up exceptions instead here
                return False
            # save the raw query into the response package
            self.geo_proxy_response.query = address[0]
            # clean up the address string to replace invalid characters
            self.address = address[0].replace(" ", "+")
        else:
            self.logger.error("A single address parameter is required within the request")
            self.geo_proxy_response.set_error(
                "A single address parameter is required within the request", "INVALID_REQUEST")
            # TODO(pickledgator): Consider bubbling up exceptions instead here
            return False

        # optional field
        service = request.get_arguments("service")
        if len(service) == 1 and service[0] in self.available_services:
                # add the desired primary service to our ordered list
            self.services.append(service[0])
            # backfill additional services from the available services as fallback
            # options after the primary
            [self.services.append(s) for s in self.find_missing_elements(
                self.available_services.keys(), self.services)]
        else:
            # if un-specified, just default the ordered services to the available services
            [self.services.append(s) for s in self.available_services.keys()]

        # optional field
        bounds = request.get_arguments("bounds")
        if len(bounds) == 1:
            coordinates = self.parse_bounding_coordinates(bounds[0])
            if coordinates:
                    # assume that geoproxy API always provides bbox as bottom_left, top_right
                    self.bounds = BoundingBox()
                    self.bounds.set_bl_tr(Coordinate(coordinates[0], coordinates[
                                          1]), Coordinate(coordinates[2], coordinates[3]))
            else:
                # leave self.bounds = None
                self.logger.warning("Error parsing bounding box coordinates")
        return True


class GeoproxyResponse:
    """Container for preparing an API response

    When a request is received by the geoproxy service, it will attempt to parse the incoming
    data, communicate with third party geocoding services and package the results (or errors) into
    a response that is sent back to the requesting client. This data structure is a container for
    that response message.

    In the event that an error occurs in the geoproxy service, the fields populated within the
    GeoproxyResponse will be: query, error, status

    In the event that no error occurs in the geoproxy service, and results are provided, the fields
    populated within the GeoproxyResponse will be: query, resolved_address, status, result

    Enum values for GeoproxyResponse.status:
    "OK" - Query was successful
    "ZERO_RESULTS" - Query was successful, but no results were obtained from third party services
    "INVALID_REQUEST" - Query was unsuccessful, there was an error in the HTTP request or parsing
    "UNKNOWN_ERROR" - Query was unsuccessful, an error not due to the request has occured
                      (eg, server not running)

    If a valid result is returned, the structure of the result dict is:
    dict(
        source: Third party service that was used to complete the query
        lat: Latitude of the geocoded result
        lon: Longitude of the geocoded result
        resolved_address: Full address of the geocoded result
    )

    Attributes:
        query (string): Original, unformatted query string from the request
        error (string): Error string if an error has occured during the request pipeline
        status (string): Enum string representing several process states (see above)
        result (dict): Geoproxy result struct (see above)

    """

    def __init__(self):
        self.query = None
        self.error = None
        self.status = None
        self.result = None

    def set_error(self, message, status_type):
        """Sets the response members associated with an error response

        Args:
            message (string): Error string
            status_type (string): One of GeoproxyResponse.status (above)

        """
        self.error = message
        self.status = status_type

    def set_result(self, source, lat, lon, resolved_address):
        """Sets the response members associated with a valid result response

        Args:
            source (string): Third party service that was used to complete the query
            lat (float): Latitude of the geocoded result
            lon (float): Longitude of the geocoded result

        """
        self.result = {'source': source, 'lat': lat, 'lon': lon,
                       'resolved_address': resolved_address}
        self.status = "OK"

    def to_json(self):
        """Converts class members into a serialized JSON object, based on status

        Returns:
            json: JSON string rep of response

        """
        d = dict()
        if self.error:
            d['error'] = self.error
            d['status'] = self.status
        else:
            d['query'] = self.query
            d['status'] = self.status
            d['result'] = self.result

        return json.dumps(d)
