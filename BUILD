load("@io_bazel_rules_docker//container:container.bzl", "container_image")

container_image(
    name = "python3_base_image",
    base = "@python3_slim_base//image",
    symlinks = {
        "/usr/bin/python": "/usr/local/bin/python",
        "/usr/bin/python3": "/usr/local/bin/python3"
    },
    visibility = ["//visibility:public"]
)
