#!/usr/bin/env python

from geoproxy.third_party_services.service_base import ThirdPartyServiceHelper
from geoproxy.third_party_services.service_base import ThirdPartyServiceResponseParser

"""Collection of classes that are associated with the Google Maps Geocoding API

Link: https://developers.google.com/maps/documentation/geocoding/intro

"""


class GoogleMapsServiceHelper(ThirdPartyServiceHelper):
    """Container for google maps query and parser
    """
    def __init__(self, google_maps_api_key):
        """Constructor

        Args:
            google_maps_api_key (string): API key for Google Maps API

        """
        super(GoogleMapsServiceHelper, self).__init__(GoogleMapsServiceResponseParser())
        self.google_maps_api_key = google_maps_api_key

    def build_query(self, address, bounds=None):
        """Generates Google Maps API query string

        Sets the base class's query member on success.

        Args:
            address (string): Valid address to search for
            bounds (BoundingBox): Bounding box parameter to include (if used)

        """
        # TODO(pickledgator): Consider bubbling up exceptions here
        self.query = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(
            address, self.google_maps_api_key)
        if bounds:
            # southwest, northeast
            self.query += "&bounds={},{}|{},{}".format(bounds.bottom_left.latitude,
                                                       bounds.bottom_left.longitude,
                                                       bounds.top_right.latitude,
                                                       bounds.top_right.longitude)


class GoogleMapsServiceResponseParser(ThirdPartyServiceResponseParser):
    """Parser specific to Google Maps Geocoder API responses
    """
    def __init__(self):
        super(GoogleMapsServiceResponseParser, self).__init__()

    def parse(self, response):
        """Parse method used to extract data from Google Maps Geocoder API response

        NOTE: If more than one result is provided in the response, we are only parsing the
        first result in that list. We are making an assumption that the third party geocoder
        is ordering the results list by the highest likelihood.

        Args:
            response (dict): JSON response as dict

        Returns:
            None/0/ThirdPartyServiceResponseParser: None if error, 0 is zero results, otherwise
                                                    parser object with populated fields

        """
        # TODO(pickledgator): Consider bubbling up exceptions here
        self.response_raw = response
        if response.get('status') == "OK":
            try:
                results = response.get('results')
                # catch empty results list (this shouldnt happen with google, but just incase)
                if len(results) == 0:
                    self.logger.warning("Service returned zero results")
                    # TODO(pickledgator): This is fragile
                    return 0
                self.logger.info("Service returned {} results for query".format(len(results)))
                # process the first result, which is the highest match likelihood
                self.address = results[0].get('formatted_address')
                location = results[0].get('geometry').get('location')
                self.latitude = float(location.get('lat'))
                self.longitude = float(location.get('lng'))
                # TODO(pickledgator): This is fragile
                return self
            except Exception as e:
                self.logger.error("Error parsing response: {}".format(e))
        # catch empty results list
        elif response.get('status') == "ZERO_RESULTS":
            self.logger.warning("Service returned zero results")
            # TODO(pickledgator): This is fragile
            return 0

        return None
