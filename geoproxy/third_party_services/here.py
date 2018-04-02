#!/usr/bin/env python

from geoproxy.third_party_services.service_base import ThirdPartyServiceHelper
from geoproxy.third_party_services.service_base import ThirdPartyServiceResponseParser

"""Collection of classes that are associated with the Here Geocoding API

Link: https://developer.here.com/documentation/geocoder/topics/what-is.html

"""


class HereServiceHelper(ThirdPartyServiceHelper):
    """Container for Here query and parser
    """
    def __init__(self, here_api_app_id, here_api_app_code):
        """Constructor

        Args:
            here_api_app_id (string): API app id for Here
            here_api_app_code (string): API app code for Here

        """
        super(HereServiceHelper, self).__init__(HereServiceResponseParser())
        self.here_api_app_id = here_api_app_id
        self.here_api_app_code = here_api_app_code

    def build_query(self, address, bounds=None):
        """Generates Here API query string

        Sets the base class's query member on success.

        Args:
            address (string): Valid address to search for
            bounds (BoundingBox): Bounding box parameter to include (if used)

        """
        # TODO(pickledgator): Consider bubbling up exceptions here
        self.query = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id={}" \
            "&app_code={}&searchtext={}".format(self.here_api_app_id,
                                                self.here_api_app_code,
                                                address)
        if bounds:
            # northwest, southeast
            self.query += "&bounds={},{};{},{}".format(bounds.top_left.latitude,
                                                       bounds.top_left.longitude,
                                                       bounds.bottom_right.latitude,
                                                       bounds.bottom_right.longitude)


class HereServiceResponseParser(ThirdPartyServiceResponseParser):
    """Parser specific to Here Geocoder API responses
    """
    def __init__(self):
        super(HereServiceResponseParser, self).__init__()

    def parse(self, response):
        """Parse method used to extract data from Here Geocoder API response

        Args:
            response (dict): JSON response as dict

        Returns:
            None/0/ThirdPartyServiceResponseParser: None if error, 0 is zero results, otherwise
                                                    parser object with populated fields

        """
        # TODO(pickledgator): Consider bubbling up exceptions here
        self.response_raw = response
        if response.get('Response'):
            try:
                view = response.get('Response').get("View")
                # catch empty results list
                if len(view) == 0:
                    self.logger.warning("Service returned zero results")
                    # TODO(pickledgator): This is fragile
                    return 0
                results = view[0].get('Result')
                self.logger.info("Service returned {} results for query".format(len(results)))
                # process the first result, which is the highest match likelihood
                location = results[0].get('Location')
                # Note: this field could have non-latin characters, we'll just pass them through
                # and let the upstream process handle encoding/decoding
                self.address = location.get("Address").get("Label")
                self.latitude = location.get("DisplayPosition").get('Latitude')
                self.longitude = location.get("DisplayPosition").get('Longitude')
                return self
            except Exception as e:
                self.logger.error("Error parsing response: {}".format(e))
        return None
