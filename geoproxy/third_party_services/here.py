#!/usr/bin/env python

from geoproxy.third_party_services.service_base import ThirdPartyServiceHelper
from geoproxy.third_party_services.service_base import ThirdPartyServiceResponseParser

class HereServiceHelper(ThirdPartyServiceHelper):
    def __init__(self, here_api_app_id, here_api_app_code):
        super(HereServiceHelper, self).__init__(HereServiceResponseParser())
        self.here_api_app_id = here_api_app_id
        self.here_api_app_code = here_api_app_code

    def set_query(self, geo_proxy_request):
        self.query = "https://geocoder.cit.api.here.com/6.2/geocode.json?app_id={}&app_code={}&searchtext={}".format(self.here_api_app_id, self.here_api_app_code, geo_proxy_request.address)
        if geo_proxy_request.bounds:
            # northwest, southeast
            self.query += "&bounds={},{};{},{}".format(geo_proxy_request.bounds.top_left.latitude, geo_proxy_request.bounds.top_left.longitude, geo_proxy_request.bounds.bottom_right.latitude, geo_proxy_request.bounds.bottom_right.longitude)


class HereServiceResponseParser(ThirdPartyServiceResponseParser):
    def __init__(self):
        super(HereServiceResponseParser, self).__init__()

    def parse(self, response):
        self.response_raw = response
        if response.get('Response'):
            try:
                view = response.get('Response').get("View")
                # catch empty results list
                if len(view) == 0:
                    self.logger.warning("Service returned zero results")
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