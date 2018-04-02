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

py_test(
    name='test_geometry',
    srcs=[
        'test/test_geometry.py',
    ],
    deps=[
        ':geoproxy_py',
    ],
    size = 'small',
)

py_test(
    name='test_third_party_services',
    srcs=[
        'test/test_third_party_services.py',
    ],
    deps=[
        ':geoproxy_py',
    ],
    size = 'small',
)

py_test(
    name='test_api',
    srcs=[
        'test/test_api.py',
    ],
    deps=[
        ':geoproxy_py',
    ],
    size = 'small',
)

py_test(
    name='test_geoproxy',
    srcs=[
        'test/test_geoproxy.py',
    ],
    deps=[
        ':geoproxy_py',
    ],
    size = 'small',
)