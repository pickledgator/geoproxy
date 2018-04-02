## Installation

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
sudo echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list
curl https://bazel.build/bazel-release.pub.gpg | apt-key add -
sudo apt-get update && apt-get install bazel python -y
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

Then, kick off bazel to pull down dependencies and setup the toolchains
```shell
bazel build examples/...
```

### Tests
Bazel can be used to run the provided unit tests
```shell
bazel test geoproxy/...
```

### Example Usage
In one terminal, run the example server with virtualenv already activated (binds to localhost:8080)
```shell
bazel-bin/examples/server
```

In another terminal, run the client with virtualenv already activated (connects to localhost:8080 by default)
```shell
bazel-bin/examples/client -q "350 5th Ave, New York, NY"
```

## API Reference

TODO

## Limitations

TODO

## Future

TODO
