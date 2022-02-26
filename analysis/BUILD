load("@pip_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "yfinance_client",
    srcs = ["yfinance_client.py"],
    deps = [
        "//protos:yfinance_py",
        requirement("pandas"),
        requirement("yfinance"),
    ],
)

py_test(
    name = "yfinance_client_test",
    srcs = ["yfinance_client_test.py"],
    deps = [":yfinance_client"],
)
