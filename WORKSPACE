# -------------------------- python ------------------------------
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "a30abdfc7126d497a7698c29c46ea9901c6392d6ed315171a6df5ce433aa4502",
    strip_prefix = "rules_python-0.6.0",
    url = "https://github.com/bazelbuild/rules_python/archive/0.6.0.tar.gz",
)

load("@rules_python//python:pip.bzl", "pip_install")

pip_install(
   name = "pip_deps",
   requirements = "//:requirements.txt",
)

# -------------------------- docker -----------------------------
## General rules
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

## rules_docker
http_archive(
    name = "io_bazel_rules_docker",
    strip_prefix = "rules_docker-0.23.0",
    urls = ["https://github.com/bazelbuild/rules_docker/releases/download/v0.23.0/rules_docker-v0.23.0.tar.gz"],
)

load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)

container_repositories()

load("@io_bazel_rules_docker//repositories:deps.bzl", container_deps = "deps")

container_deps()

load("@io_bazel_rules_docker//container:pull.bzl", "container_pull")

container_pull(
    name = "python3_slim_base",
    registry = "index.docker.io",
    repository = "python",
    tag = "3.6.10-slim-buster",
    digest = "sha256:f6383806178accdc1a321058e63c65081f29c5eb27488c5abba1e8698ebdbea9"
)

# -------------------------- docker python ------------------------------
load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py_image_repos = "repositories",
)

_py_image_repos()

# -------------------------- protobuf -----------------------------
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "com_google_protobuf",
    remote = "https://github.com/protocolbuffers/protobuf",
    tag = "v3.10.0",
)

load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")

protobuf_deps()
