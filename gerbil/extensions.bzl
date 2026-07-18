"""Bzlmod extension for native Gerbil toolchains."""

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

def _gerbil_extension_impl(module_ctx):
    names = {}
    for module in module_ctx.modules:
        for host in module.tags.host:
            if host.name in names:
                fail("duplicate Gerbil host toolchain repository: {}".format(host.name))
            names[host.name] = True
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

gerbil = module_extension(
    implementation = _gerbil_extension_impl,
    tag_classes = {"host": _host},
)
