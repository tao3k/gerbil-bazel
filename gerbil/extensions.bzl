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
    "install_digest": attr.string(mandatory = True),
    "manifest_path": attr.string(default = "gerbil-bazel-capability.json"),
    "name": attr.string(mandatory = True),
    "project_dependency_packages": attr.string_list(),
    "project_library_relative_path": attr.string(default = ".gerbil/lib"),
    "project_root_marker": attr.label(),
    "sha256": attr.string(mandatory = True),
    "strip_prefix": attr.string(),
    "urls": attr.string_list(mandatory = True),
})

_auto = tag_class(attrs = {
    "darwin_homebrew_formulae": attr.string_list(default = [
        "openssl@3",
        "sqlite",
        "zlib",
    ]),
    "dependency_roots": attr.string_list(),
    "environment": attr.string_dict(),
    "expected_version_prefixes": attr.string_list(),
    "linux_prebuilt_arch": attr.string(mandatory = True),
    "linux_prebuilt_install_digest": attr.string(mandatory = True),
    "linux_prebuilt_manifest_path": attr.string(default = "gerbil-bazel-capability.json"),
    "linux_prebuilt_sha256": attr.string(mandatory = True),
    "linux_prebuilt_strip_prefix": attr.string(),
    "linux_prebuilt_urls": attr.string_list(mandatory = True),
    "name": attr.string(default = "local_gerbil"),
    "project_dependency_packages": attr.string_list(),
    "project_library_relative_path": attr.string(default = ".gerbil/lib"),
    "project_root_marker": attr.label(),
    "tool_paths": attr.string_dict(),
})

_ARCH_ALIASES = {
    "aarch64": "aarch64",
    "amd64": "x86_64",
    "arm64": "aarch64",
    "x86_64": "x86_64",
}

def _normalized_arch(value):
    architecture = _ARCH_ALIASES.get(value.lower())
    if not architecture:
        fail("unsupported Gerbil auto-provider architecture: {}".format(value))
    return architecture

def _normalized_system(value):
    system = value.lower()
    if system in ["mac os x", "darwin"]:
        return "darwin"
    if system == "linux":
        return "linux"
    fail("Gerbil auto provider supports Darwin and Linux hosts; got {}".format(value))

def _claim_name(names, name, kind):
    if name in names:
        fail("duplicate Gerbil toolchain repository {}: {} conflicts with {}".format(
            name,
            kind,
            names[name],
        ))
    names[name] = kind

def _instantiate_auto(module_ctx, auto):
    system = _normalized_system(module_ctx.os.name)
    if system == "darwin":
        local_gerbil_repository(
            name = auto.name,
            darwin_homebrew_formulae = auto.darwin_homebrew_formulae,
            dependency_roots = auto.dependency_roots,
            environment = auto.environment,
            expected_version_prefixes = auto.expected_version_prefixes,
            project_dependency_packages = auto.project_dependency_packages,
            project_library_relative_path = auto.project_library_relative_path,
            project_root_marker = auto.project_root_marker,
            tool_paths = auto.tool_paths,
        )
        return

    host_arch = _normalized_arch(module_ctx.os.arch)
    prebuilt_arch = _normalized_arch(auto.linux_prebuilt_arch)
    if host_arch != prebuilt_arch:
        fail(
            "Gerbil auto provider {} declares Linux prebuilt architecture {} but the host is {}".format(
                auto.name,
                prebuilt_arch,
                host_arch,
            ),
        )
    prebuilt_gerbil_repository(
        name = auto.name,
        darwin_homebrew_formulae = auto.darwin_homebrew_formulae,
        environment = auto.environment,
        expected_version_prefixes = auto.expected_version_prefixes,
        install_digest = auto.linux_prebuilt_install_digest,
        manifest_path = auto.linux_prebuilt_manifest_path,
        project_dependency_packages = auto.project_dependency_packages,
        project_library_relative_path = auto.project_library_relative_path,
        project_root_marker = auto.project_root_marker,
        sha256 = auto.linux_prebuilt_sha256,
        strip_prefix = auto.linux_prebuilt_strip_prefix,
        urls = auto.linux_prebuilt_urls,
    )

def _gerbil_extension_impl(module_ctx):
    names = {}
    for module in module_ctx.modules:
        for auto in module.tags.auto:
            _claim_name(names, auto.name, "auto")
            _instantiate_auto(module_ctx, auto)
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
                install_digest = prebuilt.install_digest,
                manifest_path = prebuilt.manifest_path,
                project_dependency_packages = prebuilt.project_dependency_packages,
                project_library_relative_path = prebuilt.project_library_relative_path,
                project_root_marker = prebuilt.project_root_marker,
                sha256 = prebuilt.sha256,
                strip_prefix = prebuilt.strip_prefix,
                urls = prebuilt.urls,
            )

gerbil = module_extension(
    implementation = _gerbil_extension_impl,
    arch_dependent = True,
    os_dependent = True,
    tag_classes = {
        "auto": _auto,
        "host": _host,
        "prebuilt": _prebuilt,
    },
)
