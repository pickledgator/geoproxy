load("@geoproxy_pip_deps//:requirements.bzl", "requirement")

py_library(
    name = "geoproxy_py",
    srcs = [
        "__init__.py",
        "api.py",
        "geometry.py",
        "handlers/geoproxy_request.py",
        "third_party_services/google_maps.py",
        "third_party_services/here.py",
        "third_party_services/service_base.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        requirement("tornado"),
    ],
    srcs_version = 'PY3',
)