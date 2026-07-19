"""Host capability discovery for local Gerbil toolchains."""

_EXEC_CONSTRAINT_BY_SYSTEM = {
    "darwin": "@platforms//os:macos",
    "linux": "@platforms//os:linux",
}

def _checked(repository_ctx, argv, description):
    result = repository_ctx.execute(argv, quiet = True)
    if result.return_code != 0:
        fail("{} failed (exit {}): {}".format(
            description,
            result.return_code,
            result.stderr.strip(),
        ))
    return result.stdout.strip()

def _which(repository_ctx, candidates, capability):
    for candidate in candidates:
        path = repository_ctx.which(candidate)
        if path:
            return str(path)
    fail("Gerbil Bazel could not resolve {} from candidates: {}".format(
        capability,
        ", ".join(candidates),
    ))

def _environment_tool(repository_ctx, key, fallback, capability):
    value = repository_ctx.os.environ.get(key, "")
    if not value:
        return fallback
    if value.startswith("/"):
        if not repository_ctx.path(value).exists:
            fail("{} points to a missing {}: {}".format(key, capability, value))
        return value
    return _which(repository_ctx, [value], "{} from {}".format(capability, key))

def _darwin_checked(
        repository_ctx,
        argv,
        description,
        developer_dir = "",
        sdkroot = ""):
    command = [
        "/usr/bin/env",
        "-u",
        "DEVELOPER_DIR",
        "-u",
        "SDKROOT",
    ]
    if developer_dir:
        command.append("DEVELOPER_DIR=" + developer_dir)
    if sdkroot:
        command.append("SDKROOT=" + sdkroot)
    return _checked(repository_ctx, command + argv, description)

def _join_host_path(repository_ctx, key, discovered):
    values = list(discovered)
    inherited = repository_ctx.os.environ.get(key, "")
    if inherited:
        values.append(inherited)
    return ":".join(values)

def _darwin_homebrew_environment(repository_ctx, formulae):
    brew = repository_ctx.which("brew")
    if not brew:
        return {}

    include_paths = []
    library_paths = []
    pkg_config_paths = []
    for formula in formulae:
        result = repository_ctx.execute([str(brew), "--prefix", formula], quiet = True)
        if result.return_code != 0:
            continue
        prefix = result.stdout.strip()
        include_path = prefix + "/include"
        library_path = prefix + "/lib"
        pkg_config_path = library_path + "/pkgconfig"
        if repository_ctx.path(include_path).exists:
            include_paths.append(include_path)
        if repository_ctx.path(library_path).exists:
            library_paths.append(library_path)
        if repository_ctx.path(pkg_config_path).exists:
            pkg_config_paths.append(pkg_config_path)

    environment = {}
    if include_paths:
        environment["CPATH"] = _join_host_path(repository_ctx, "CPATH", include_paths)
    if library_paths:
        environment["LIBRARY_PATH"] = _join_host_path(repository_ctx, "LIBRARY_PATH", library_paths)
        ldflags = ["-L{}".format(path) for path in library_paths]
        inherited_ldflags = repository_ctx.os.environ.get("LDFLAGS", "")
        if inherited_ldflags:
            ldflags.append(inherited_ldflags)
        environment["LDFLAGS"] = " ".join(ldflags)
    if pkg_config_paths:
        environment["PKG_CONFIG_PATH"] = _join_host_path(
            repository_ctx,
            "PKG_CONFIG_PATH",
            pkg_config_paths,
        )
    return environment

def _darwin_environment(repository_ctx, homebrew_formulae):
    developer_dir = repository_ctx.os.environ.get("GERBIL_DEVELOPER_DIR", "")
    if not developer_dir:
        developer_dir = _darwin_checked(
            repository_ctx,
            ["/usr/bin/xcode-select", "-p"],
            "xcode-select",
        )

    sdkroot = repository_ctx.os.environ.get("GERBIL_SDKROOT", "")
    if not sdkroot:
        sdkroot = _darwin_checked(
            repository_ctx,
            ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"],
            "macOS SDK discovery",
            developer_dir = developer_dir,
        )

    discovered_tools = {}
    for name in ["ar", "as", "clang", "clang++", "ld"]:
        discovered_tools[name] = _darwin_checked(
            repository_ctx,
            ["/usr/bin/xcrun", "--sdk", "macosx", "--find", name],
            "macOS {} discovery".format(name),
            developer_dir = developer_dir,
            sdkroot = sdkroot,
        )
    memory = _checked(
        repository_ctx,
        ["/usr/sbin/sysctl", "-n", "hw.memsize"],
        "Darwin memory discovery",
    )
    cpu_count = _checked(
        repository_ctx,
        ["/usr/sbin/sysctl", "-n", "hw.logicalcpu"],
        "Darwin logical CPU discovery",
    )

    environment = _darwin_homebrew_environment(repository_ctx, homebrew_formulae)
    environment.update({
        "AR": discovered_tools["ar"],
        "CXX": discovered_tools["clang++"],
        "DEVELOPER_DIR": developer_dir,
        "SDKROOT": sdkroot,
    })

    return struct(
        environment = environment,
        gerbil_as = discovered_tools["as"],
        gerbil_cc = discovered_tools["clang"],
        gerbil_ld = discovered_tools["ld"],
        system_cpu_count = cpu_count,
        system_memory_bytes = memory,
    )

def _linux_environment(repository_ctx):
    pages = _checked(
        repository_ctx,
        ["getconf", "_PHYS_PAGES"],
        "Linux physical page discovery",
    )
    page_size = _checked(
        repository_ctx,
        ["getconf", "PAGE_SIZE"],
        "Linux page-size discovery",
    )
    cpu_count = _checked(
        repository_ctx,
        ["getconf", "_NPROCESSORS_ONLN"],
        "Linux logical CPU discovery",
    )
    return struct(
        environment = {},
        gerbil_as = _which(repository_ctx, ["as"], "assembler"),
        gerbil_cc = _which(repository_ctx, ["cc", "clang", "gcc"], "C compiler"),
        gerbil_ld = _which(repository_ctx, ["ld"], "linker"),
        system_cpu_count = cpu_count,
        system_memory_bytes = str(int(pages) * int(page_size)),
    )

def resolve_gerbil_build_cores(
        repository_ctx,
        declared_environment,
        system_cpu_count):
    """Resolves the upstream std/make worker count and its provenance."""
    value = repository_ctx.os.environ.get("GERBIL_BUILD_CORES", "")
    source = "process-environment"
    if not value:
        value = declared_environment.get("GERBIL_BUILD_CORES", "")
        source = "repository-environment"
    if not value:
        value = system_cpu_count
        source = "host-system"

    for character in value.elems():
        if character not in "0123456789":
            fail("GERBIL_BUILD_CORES must be a positive integer, got {!r}".format(value))
    count = int(value)
    if count < 1:
        fail("GERBIL_BUILD_CORES must be a positive integer, got {!r}".format(value))
    return struct(
        source = source,
        value = str(count),
    )

def resolve_host_environment(repository_ctx, darwin_homebrew_formulae = []):
    """Returns normalized host capabilities for Darwin or Linux."""
    system = repository_ctx.os.name.lower()
    if system in ["mac os x", "darwin"]:
        system = "darwin"
        host = _darwin_environment(repository_ctx, darwin_homebrew_formulae)
    elif system == "linux":
        host = _linux_environment(repository_ctx)
    else:
        fail("Gerbil Bazel supports Darwin and Linux hosts; got {}".format(
            repository_ctx.os.name,
        ))

    environment = dict(host.environment)
    environment["PATH"] = repository_ctx.os.environ.get("PATH", "")
    compiler = repository_ctx.os.environ.get("GERBIL_CC", "")
    if compiler:
        compiler = _environment_tool(
            repository_ctx,
            "GERBIL_CC",
            "",
            "C compiler",
        )
    else:
        compiler = host.gerbil_cc

    return struct(
        environment = environment,
        exec_constraint = _EXEC_CONSTRAINT_BY_SYSTEM[system],
        gerbil_as = _environment_tool(
            repository_ctx,
            "GERBIL_AS",
            host.gerbil_as,
            "assembler",
        ),
        gerbil_cc = compiler,
        gerbil_ld = _environment_tool(
            repository_ctx,
            "GERBIL_LD",
            host.gerbil_ld,
            "linker",
        ),
        system = system,
        system_cpu_count = host.system_cpu_count,
        system_memory_bytes = host.system_memory_bytes,
    )
