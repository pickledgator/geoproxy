#!/usr/bin/env python

import argparse
import json
import socket
import urllib.request
import urllib.error

def main():
    # Parse arguments from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", default="localhost", help="IP address of the server (default: localhost)")
    parser.add_argument("-p", "--port", default=8080, help="Port of the server (default: 8080)")
    parser.add_argument("-q", "--query", required=True, help="Query string to geocode, quoted")
    parser.add_argument("-s", "--service", help="Primary third party service to use (falls back on other available services automatically (options: google/here) (default: google)")
    parser.add_argument("-b", "--bounds", help="Bounds for viewport (external service corner ordering: \"lat,long|lat,long\")")
    args = parser.parse_args()

    query = "http://{}:{}/geocode?address={}".format(args.address, args.port, args.query)
    # optionally add bounds
    if args.bounds:
        query += "&bounds={}".format(args.bounds)
    # optionally add primary service
    if args.service:
        query += "&service={}".format(args.service)
    # clean up the query string and remove spaces to properly format request
    query = query.replace(" ","+")

    print("Sending query: {}".format(query))

    response = None
    try:
        response = urllib.request.urlopen(query, timeout=2).read().decode('utf-8')
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        print("Error in request: {}".format(error))
    except socket.timeout:
        print("Timeout in request")

    # if our response succeeds, then parse it and pass the parser back upstream
    if response:
        response_json = json.loads(response)
        print(json.dumps(response_json, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()