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
                tool_paths = host.tool_paths,
            )

gerbil = module_extension(
    implementation = _gerbil_extension_impl,
    tag_classes = {"host": _host},
)
