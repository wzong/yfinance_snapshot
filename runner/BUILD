load("@io_bazel_rules_docker//container:container.bzl", "container_image", "container_push")
load("@io_bazel_rules_docker//python3:image.bzl", "py3_image")
load("@pip_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "snapshot_lib",
    srcs = ["snapshot.py"],
    deps = [
        "//analysis:yfinance_client",
        "//protos:yfinance_py",
        "//storage:sqlite",
    ],
)

py_binary(
    name = "snapshot",
    srcs = ["snapshot.py"],
    deps = [":snapshot_lib"],
)

py3_image(
    name = "snapshot_image",
    srcs = ["snapshot.py"],
    base = "//:python3_base_image",
    layers = [":snapshot_lib"],
    main = "snapshot.py",
)

container_push(
	name = "push_snapshot_image",
	format = "Docker",
	image = ":snapshot_image",
	repository = "wzong/yfinance-snapshot",
    registry = "index.docker.io",
	tag = "latest",
)
