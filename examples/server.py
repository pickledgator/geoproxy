#!/usr/bin/env python

import argparse
import logging
import os
from tornado.ioloop import IOLoop

from geoproxy import Geoproxy

logging.basicConfig(
    format="[%(asctime)s][%(name)s](%(levelname)s) %(message)s", level=logging.DEBUG)


def main():
    # Parse arguments from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", default="localhost",
                        help="IP address where the service is running (default: localhost)")
    parser.add_argument("-p", "--port", default=8080,
                        help="Port that the service runs on (default: 8080)")
    args = parser.parse_args()

    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    here_api_app_id = os.environ.get('HERE_API_APP_ID')
    here_api_app_code = os.environ.get('HERE_API_APP_CODE')

    # Create server object and tell it to listen on the desired port
    geo_proxy = Geoproxy(args.address, args.port, google_maps_api_key,
                         here_api_app_id, here_api_app_code)

    try:
        # start the ioloop
        IOLoop.instance().start()
    except KeyboardInterrupt:
        # ensure that the event loop stops cleanly on interrupt
        IOLoop.instance().stop()


if __name__ == "__main__":
    main()
