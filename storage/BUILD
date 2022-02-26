load("@pip_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "sqlite",
    srcs = ["sqlite.py"],
)

py_test(
    name = "sqlite_test",
    srcs = ["sqlite_test.py"],
    deps = [":sqlite"],
)
