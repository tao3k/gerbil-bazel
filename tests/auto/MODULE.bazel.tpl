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
    linux_prebuilt_sha256 = "@@ARCHIVE_SHA256@@",
    linux_prebuilt_urls = ["@@ARCHIVE_URL@@"],
    tool_paths = @@HOST_TOOL_PATHS@@,
)
use_repo(gerbil, "auto_gerbil")

register_toolchains("@auto_gerbil//:registered_toolchain")
