# Geoproxy
A geocoding proxy server for multiple third-party geocoding services.

## Overview
Geocoding is the process of converting addresses (like "1600 Amphitheatre Parkway, Mountain View, CA") into geographic coordinates (like latitude 37.423021 and longitude -122.083739).

Geoproxy is a simple network service that resolves the latitude and longitude coordinates for a specified address using third party geocoding services such as [Google Maps Geocoder](https://developers.google.com/maps/documentation/geocoding/intro) or [Here Geocoder](https://developer.here.com/documentation/geocoder/topics/what-is.html). Geoproxy will attempt to resolve an input address using a primary third party geocoding service, and fall back onto backup third party geocoding services, should others fail.

Geoproxy provides a RESTful HTTP interface and JSON serialized responses.

## Installation

### Obtain third-party geocoder api keys
Geoproxy uses two third party geocoding services within the proxy. You should first obtain API keys for each of the services.
* [Google Maps Geocoder](https://developers.google.com/maps/documentation/geocoding/intro)
* [Here Geocoder](https://developer.here.com/documentation/geocoder/topics/what-is.html)

### OSX Setup
First start with system dependencies for the build system
```shell
brew install bazel
pip3 install virtualenv
```

### Linux (Ubuntu 16.04) Setup
First start with system dependencies for the build system
```shell
sudo apt-get update && apt-get install openjdk-8-jdk curl -y
sudo echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add -
sudo apt-get update && apt-get install bazel python python-pip3 -y
pip3 install virtualenv
```

### Clone and Build
Then, clone the project and setup a virtual env to work within
```shell
git clone https://github.com/pickledgator/geoproxy
cd geoproxy
virtualenv -p python3 env
source env/bin/activate
```

Then, kick off bazel to pull down dependencies and package the library.
```shell
bazel build geoproxy/...
```

### Tests
Bazel can be used to run the provided unit tests
```shell
bazel test geoproxy/...
```

### Example Usage
An example client and server application are provided in this project. In order to run them, you'll need to first, set both Google Maps and Here API keys as environment variables. These keys are used by geoproxy to connect to third party geocoding services.
```shell
export GOOGLE_MAPS_API_KEY=??
export HERE_API_APP_ID=??
export HERE_API_APP_CODE=??
```

Next you'll need to build the examples.
```shell
bazel build examples/...
```

In one terminal, run the example server with virtualenv already activated. The server application supports the following command line arguments: `-a`: The ip address of the server (default: localhost), `-p`: The port the server should bind to (default: 8080).
```shell
source env/bin/activate
bazel-bin/examples/server -a localhost -p 8080
```

In another terminal, run the client with virtualenv already activated. The client application supports the following command line arguemnts: `-a`: The ip address of the server (default: localhost), `-p`: The port the server is bound to (default: 8080), `-q`: The address string to geocode (in quotes), `-s`: (optional) The primary service to use (default: google), `-b`: (optional) The bounds string (in quotes) to pass to the geocoder in the format that the third party geocoder expects (see API Reference).
```shell
source env/bin/activate
bazel-bin/examples/client -q "350 5th Ave, New York"
bazel-bin/examples/client -a localhost -p 8080 -q "Winnetka" -s "here" -b "34.172684,-118.604794|34.236144,-118.500938"
```

## API Reference
### Geoproxy Requests
A Geoproxy API request takes the following form:
```
http://ipaddress:port/geocode?parameters
```
where `address` is the ip address of the server and `port` is the port that the server it bound to.

Currently only `http` connections are supported, `https` is not supported.

Note: URLs must be properly encoded to be valid and are limited to 8192 characters for all web services. Some parameters are required while some are optional. As is standard in URLs, parameters are separated using the `&` character. Parameters should use `+` instead of spaces since spaces would result in an invalid HTTP request.

#### Parameters
##### Required parameters
* `address` - The street address that you want to geocode, in the format used by the national postal service of the country concerned.

##### Optional parameters
* `service` - The primary third party service to be used. Valid options include: `google` and `here`. 
    * When this optional parameter is specified, the first third party service requested will be the value specified by this parameter. 
    * The fallback third party services are then populated with any remaining supported services (whatever is left, sorted alphabetically). If the service parameter is not specified, all available third party services will be used in alphabetical order.
* `bounds` - The bounding box coordinates used to bias/influence the geocoding results. 
    * The bounds specification should be formatted as `bounds=bottom_left.latitude,bottom_left.longitude|top_right.latitude,top_right.longitude`
    * The general format is latitude of coordinate 1, comma (`,`), longitude of coordinate 1, a pipe (`|`), latitude of coordinate 2, comma (`,`), longitude of coordinate 2.
    * If a different servive is used, eg, `here`, the bounds will automatically be recomputed internally to match the third party service's expected format.

### Geoproxy Responses
Responses are returned as JSON serialized strings. For example, consider the following request:
```
http://localhost:8080/geocode?address=350+5th+Ave,+NY
```

The expected response would be:
```json
{
    "query": "350 5th Ave, NY",
    "result": {
        "lat": 40.7484799,
        "lon": -73.9854245,
        "resolved_address": "350 5th Ave, New York, NY 10118, USA",
        "source": "google"
    },
    "status": "OK"
}
```

Note that the response contains several elements:
* `query` - Original query string passed to geoproxy
* `status` - Contains metadata about the response (see codes below)
* `result` - Information about the top geocode result. This field will only be present if `status` is `OK`

When geoproxy returns a status code other than `OK`, there may be an additional `error` field within the response object. This field contains more detailed information about the reasons behind the given status code. This field is not gaurunteed to be present. 

#### Status Codes
The status field within the geoproxy response object contains the status of the request and may contain debugging information if geoproxy should fail. The status element may contain the following values:
* `OK` - No errors, result is provided
* `ZERO_RESULTS` - All third party geocoding services returned zero results.
* `INVALID_REQUEST` - The geoproxy request was invalid or had an error during parsing.
* `UNKNOWN_ERROR` - The request could not be completed due to a server error.

#### Result
When geoproxy returns a valid result, it will be populated with the following members:
* `lat` - The latitude of the geocoded location
* `lon` - The longitude of the geocoded location
* `resolved_address` - The full address string of the geocoded location
* `source` - Which third party geocoding service was used to populate the result

## Limitations
There are several known limitations in the implementation of the geoproxy service. They are listed below.
* No authentification
* No spam protection
* Limited robustness to non-latin characters
* Limited exception handling
* The result returned is the first item found (ie, first geocoder to return a list of results, where the first item in the list is chosen)
* Not all third party geocoding service parameters are supported yet (only bounds/bbox)

# Testing
Geoproxy has been tested on:
* MacOS 10.13.3 using python 3.6.4 and bazel 0.11.1
