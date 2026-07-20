module(name = "gerbil_auto_consumer_test")

bazel_dep(name = "gerbil_bazel", version = "0.1.0")
local_path_override(
    module_name = "gerbil_bazel",
    path = "@@GERBIL_BAZEL_PATH@@",
)

gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.auto(
    name = "auto_gerbil",
    linux_prebuilt_arch = "@@ARCHITECTURE@@",
    linux_prebuilt_install_digest = "@@INSTALL_DIGEST@@",
    linux_prebuilt_sha256 = "@@ARCHIVE_SHA256@@",
    linux_prebuilt_urls = ["@@ARCHIVE_URL@@"],
    project_dependency_packages = ["clan", "gslph", "missing-package"],
    project_library_relative_path = ".gerbil/lib",
    project_root_marker = "//:project-root.marker",
    tool_paths = @@HOST_TOOL_PATHS@@,
)
use_repo(gerbil, "auto_gerbil")

register_toolchains("@auto_gerbil//:registered_toolchain")
