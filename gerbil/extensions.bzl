"""Bzlmod extension for native Gerbil toolchains."""

load(":prebuilt_repository.bzl", "prebuilt_gerbil_repository")
load(":repository.bzl", "local_gerbil_repository")

_host = tag_class(attrs = {
    "darwin_homebrew_formulae": attr.string_list(default = [
        "openssl@3",
        "sqlite",
        "zlib",
    ]),
    "dependency_roots": attr.string_list(),
    "environment": attr.string_dict(),
    "expected_version_prefixes": attr.string_list(),
    "name": attr.string(default = "local_gerbil"),
    "project_dependency_packages": attr.string_list(),
    "project_library_relative_path": attr.string(default = ".gerbil/lib"),
    "project_root_marker": attr.label(),
    "tool_paths": attr.string_dict(),
})

_prebuilt = tag_class(attrs = {
    "darwin_homebrew_formulae": attr.string_list(default = [
        "openssl@3",
        "sqlite",
        "zlib",
    ]),
    "environment": attr.string_dict(),
    "expected_version_prefixes": attr.string_list(),
    "manifest_path": attr.string(default = "gerbil-bazel-capability.json"),
    "name": attr.string(mandatory = True),
    "sha256": attr.string(mandatory = True),
    "strip_prefix": attr.string(),
    "urls": attr.string_list(mandatory = True),
})

def _claim_name(names, name, kind):
    if name in names:
        fail("duplicate Gerbil toolchain repository {}: {} conflicts with {}".format(
            name,
            kind,
            names[name],
        ))
    names[name] = kind

def _gerbil_extension_impl(module_ctx):
    names = {}
    for module in module_ctx.modules:
        for host in module.tags.host:
            _claim_name(names, host.name, "host")
            local_gerbil_repository(
                name = host.name,
                darwin_homebrew_formulae = host.darwin_homebrew_formulae,
                dependency_roots = host.dependency_roots,
                environment = host.environment,
                expected_version_prefixes = host.expected_version_prefixes,
                project_dependency_packages = host.project_dependency_packages,
                project_library_relative_path = host.project_library_relative_path,
                project_root_marker = host.project_root_marker,
                tool_paths = host.tool_paths,
            )
        for prebuilt in module.tags.prebuilt:
            _claim_name(names, prebuilt.name, "prebuilt")
            prebuilt_gerbil_repository(
                name = prebuilt.name,
                darwin_homebrew_formulae = prebuilt.darwin_homebrew_formulae,
                environment = prebuilt.environment,
                expected_version_prefixes = prebuilt.expected_version_prefixes,
                manifest_path = prebuilt.manifest_path,
                sha256 = prebuilt.sha256,
                strip_prefix = prebuilt.strip_prefix,
                urls = prebuilt.urls,
            )

gerbil = module_extension(
    implementation = _gerbil_extension_impl,
    tag_classes = {
        "host": _host,
        "prebuilt": _prebuilt,
    },
)
