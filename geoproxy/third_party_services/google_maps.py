#!/usr/bin/env python

from geoproxy.third_party_services.service_base import ThirdPartyServiceHelper
from geoproxy.third_party_services.service_base import ThirdPartyServiceResponseParser

class GoogleMapsServiceHelper(ThirdPartyServiceHelper):
    def __init__(self, google_maps_api_key):
        super(GoogleMapsServiceHelper, self).__init__(GoogleMapsServiceResponseParser())
        self.google_maps_api_key = google_maps_api_key

    def set_query(self, geo_proxy_request):
        self.query = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(geo_proxy_request.address, self.google_maps_api_key)
        if geo_proxy_request.bounds:
            # southwest, northeast
            self.query += "&bounds={},{}|{},{}".format(geo_proxy_request.bounds.bottom_left.latitude, geo_proxy_request.bounds.bottom_left.longitude, geo_proxy_request.bounds.top_right.latitude, geo_proxy_request.bounds.top_right.longitude)


class GoogleMapsServiceResponseParser(ThirdPartyServiceResponseParser):
    def __init__(self):
        super(GoogleMapsServiceResponseParser, self).__init__()

    def parse(self, response):
        self.response_raw = response
        if response.get('status') == "OK":
            try:
                results = response.get('results')
                # catch empty results list (this shouldnt happen with google, but just incase)
                if len(results) == 0:
                    self.logger.warning("Service returned zero results")
                    return 0
                self.logger.info("Service returned {} results for query".format(len(results)))
                # process the first result, which is the highest match likelihood
                self.address = results[0].get('formatted_address')
                location = results[0].get('geometry').get('location')
                self.latitude = location.get('lat')
                self.longitude = location.get('lng')
                return self
            except Exception as e:
                self.logger.error("Error parsing response: {}".format(e))
        # catch empty results list
        elif response.get('status') == "ZERO_RESULTS":
            self.logger.warning("Service returned zero results")
            return 0

        return None