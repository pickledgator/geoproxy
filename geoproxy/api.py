#!/usr/bin/env python

import json
import logging

from geoproxy.geometry import BoundingBox
from geoproxy.geometry import Coordinate

class GeoproxyRequestParser:
    def __init__(self, available_services, geo_proxy_response):
        self.logger = logging.getLogger(self.__class__.__name__)
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
        return list(set(full_list) - set(partial_list))

    def parse(self, request):
        # required field
        address = request.get_arguments("address")
        if len(address) == 1:
            # verify that the address field is not empty
            if address[0] == "":
                self.logger.error("Address is invalid")
                self.geo_proxy_response.set_error("Address is invalid", "INVALID_REQUEST")
                return False
            # save the raw query into the response package
            self.geo_proxy_response.query = address[0]
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


class GeoproxyResponse:
    """Help package an API response

    Valid status messages:
    "OK"
    "ZERO_RESULTS"
    "INVALID_REQUEST"
    "UNKNOWN_ERROR"

    """
    def __init__(self):
        self.query = None
        self.resolved_address = None
        self.error = None
        self.status = None
        self.result = None

    def set_error(self, message, status_type):
        self.error = message
        self.status = status_type

    def set_result(self, source, lat, lon, resolved_address):
        self.resolved_address = resolved_address
        self.result = {'source': source, 'lat': lat, 'lon': lon}
        self.status = "OK"

    def to_json(self):
        d = dict()
        if self.error:
            d['error'] = self.error
            d['status'] = self.status
        else:
            d['query'] = self.query
            d['resolved_address'] = self.resolved_address
            d['status'] = self.status
            d['result'] = self.result

        return json.dumps(d)