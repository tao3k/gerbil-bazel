module(name = "gerbil_prebuilt_consumer_test")

bazel_dep(name = "gerbil_bazel", version = "0.1.0")
local_path_override(
    module_name = "gerbil_bazel",
    path = "@@GERBIL_BAZEL_PATH@@",
)

gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.prebuilt(
    install_digest = "@@INSTALL_DIGEST@@",
    name = "prebuilt_gerbil",
    project_dependency_packages = ["clan", "gslph", "missing-package"],
    project_library_relative_path = ".gerbil/lib",
    project_root_marker = "//:project-root.marker",
    sha256 = "@@ARCHIVE_SHA256@@",
    urls = ["@@ARCHIVE_URL@@"],
)
use_repo(gerbil, "prebuilt_gerbil")

register_toolchains("@prebuilt_gerbil//:registered_toolchain")
