"""Repository rule for discovering a native Gerbil installation."""

load(":host_system.bzl", "resolve_host_environment")

_GERBIL_TOOLS = {
    "gxc": ["gxc"],
    "gxi": ["gxi"],
    "gxpkg": ["gxpkg"],
    "gxtest": ["gxtest"],
}

def _shell_quote(value):
    return "'{}'".format(value.replace("'", "'\"'\"'"))

def _resolve_tools(repository_ctx):
    tools = {}
    for name, candidates in _GERBIL_TOOLS.items():
        declared = repository_ctx.attr.tool_paths.get(name, "")
        if declared:
            tools[name] = declared
            continue
        override = repository_ctx.os.environ.get("GERBIL_{}".format(name.upper()), "")
        if override:
            tools[name] = override
            continue
        for candidate in candidates:
            path = repository_ctx.which(candidate)
            if path:
                tools[name] = str(path)
                break
        if name not in tools:
            fail("Gerbil Bazel could not resolve {} on PATH".format(name))
    return tools

def _gerbil_version(repository_ctx, tools):
    result = repository_ctx.execute([tools["gxi"], "-v"], quiet = True)
    if result.return_code != 0:
        fail("Gerbil version discovery failed: {}".format(result.stderr.strip()))
    version = result.stdout.strip()
    expected = repository_ctx.attr.expected_version_prefixes
    if expected:
        accepted = False
        for prefix in expected:
            if version.startswith("Gerbil v" + prefix) or version.startswith(prefix):
                accepted = True
                break
        if not accepted:
            fail("Gerbil version {!r} does not match accepted prefixes {}".format(
                version,
                expected,
            ))
    return version

def _environment_exports(environment):
    lines = []
    for key in sorted(environment.keys()):
        lines.append("export {}={}".format(key, _shell_quote(environment[key])))
    return "\n".join(lines)

def _environment_dict(environment):
    entries = []
    for key in sorted(environment.keys()):
        entries.append("        {}: {},".format(repr(key), repr(environment[key])))
    if not entries:
        return "{}"
    return "{\n" + "\n".join(entries) + "\n    }"

def _tool_rules():
    rules = []
    for name in sorted(_GERBIL_TOOLS.keys()):
        rules.append("""sh_binary(
    name = {name},
    srcs = [{wrapper}],
    data = [{raw}, \"native_abi.txt\"],
)""".format(
            name = repr(name),
            raw = repr("bin/{}_raw".format(name)),
            wrapper = repr("{}.sh".format(name)),
        ))
    return "\n\n".join(rules)

def _fingerprint(repository_ctx, host, tools):
    override = repository_ctx.os.environ.get("GERBIL_NATIVE_ABI", "")
    if override:
        return override
    result = repository_ctx.execute(
        ["/usr/bin/env", "bash", str(repository_ctx.path(repository_ctx.attr._native_abi_probe))] + [
            tools["gxi"],
            tools["gxc"],
            tools["gxpkg"],
            tools["gxtest"],
            host.gerbil_cc,
            host.gerbil_as,
            host.gerbil_ld,
        ],
        quiet = True,
    )
    if result.return_code != 0:
        fail("Gerbil native ABI discovery failed: {}".format(result.stderr.strip()))
    fingerprint = result.stdout.strip()
    if len(fingerprint) != 40:
        fail("Gerbil native ABI fingerprint must be 40 hexadecimal characters")
    return fingerprint

def _link_dependency_roots(repository_ctx):
    repository_ctx.file("lib/.root", "gerbil-bazel dependency root\n")
    for index, root in enumerate(repository_ctx.attr.dependency_roots):
        path = repository_ctx.path(root)
        if not path.exists:
            fail("Gerbil dependency root does not exist: {}".format(root))
        repository_ctx.symlink(path, "lib/dependency-{}".format(index))

def _local_gerbil_repository_impl(repository_ctx):
    host = resolve_host_environment(
        repository_ctx,
        darwin_homebrew_formulae = repository_ctx.attr.darwin_homebrew_formulae,
    )
    tools = _resolve_tools(repository_ctx)
    version = _gerbil_version(repository_ctx, tools)
    fingerprint = _fingerprint(repository_ctx, host, tools)
    environment = dict(host.environment)
    environment.update(repository_ctx.attr.environment)
    environment["CC"] = host.gerbil_cc
    environment["GERBIL_BAZEL_CPU_COUNT"] = host.system_cpu_count
    environment["GERBIL_BAZEL_MEMORY_BYTES"] = host.system_memory_bytes
    for name in ["AR", "CXX"]:
        value = repository_ctx.os.environ.get(name, "")
        if value:
            environment[name] = value

    substitutions = {
        "{{ENVIRONMENT}}": _environment_exports(environment),
        "{{NATIVE_ABI}}": _shell_quote(fingerprint),
    }
    repository_ctx.template(
        "native_scheme_env.sh",
        repository_ctx.attr._native_scheme_env_template,
        substitutions,
        executable = True,
    )

    for name, path in tools.items():
        repository_ctx.symlink(path, "bin/{}_raw".format(name))
        tool_substitutions = dict(substitutions)
        tool_substitutions["{{TOOL}}"] = _shell_quote(path)
        repository_ctx.template(
            "{}.sh".format(name),
            repository_ctx.attr._native_tool_template,
            tool_substitutions,
            executable = True,
        )

    _link_dependency_roots(repository_ctx)
    repository_ctx.file("native_abi.txt", fingerprint + "\n")
    repository_ctx.file(
        "toolchain.receipt.json",
        json.encode_indent({
            "environment": environment,
            "nativeAbiFingerprint": fingerprint,
            "schema": "gerbil-bazel.local-toolchain-receipt.v1",
            "system": host.system,
            "systemCpuCount": int(host.system_cpu_count),
            "systemMemoryBytes": int(host.system_memory_bytes),
            "tools": tools,
            "version": version,
        }, indent = "  ") + "\n",
    )
    repository_ctx.template(
        "BUILD.bazel",
        repository_ctx.attr._build_template,
        {
            "{{ENVIRONMENT_DICT}}": _environment_dict(environment),
            "{{EXEC_CONSTRAINT}}": repr(host.exec_constraint),
            "{{GERBIL_AS}}": repr(host.gerbil_as),
            "{{GERBIL_CC}}": repr(host.gerbil_cc),
            "{{GERBIL_LD}}": repr(host.gerbil_ld),
            "{{NATIVE_ABI}}": repr(fingerprint),
            "{{SYSTEM_CPU_COUNT}}": repr(host.system_cpu_count),
            "{{SYSTEM_MEMORY_BYTES}}": repr(host.system_memory_bytes),
            "{{TOOL_RULES}}": _tool_rules(),
        },
    )

local_gerbil_repository = repository_rule(
    implementation = _local_gerbil_repository_impl,
    attrs = {
        "darwin_homebrew_formulae": attr.string_list(default = [
            "openssl@3",
            "sqlite",
            "zlib",
        ]),
        "dependency_roots": attr.string_list(),
        "environment": attr.string_dict(),
        "expected_version_prefixes": attr.string_list(),
        "tool_paths": attr.string_dict(),
        "_build_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:local_toolchain.BUILD.bazel.tpl",
        ),
        "_native_abi_probe": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:native_abi_fingerprint.sh",
        ),
        "_native_scheme_env_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:native_scheme_env.sh.tpl",
        ),
        "_native_tool_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:native_tool.sh.tpl",
        ),
    },
    environ = [
        "AR",
        "CC",
        "CPATH",
        "CXX",
        "GERBIL_AS",
        "GERBIL_CC",
        "GERBIL_DEVELOPER_DIR",
        "GERBIL_GXC",
        "GERBIL_GXI",
        "GERBIL_GXPKG",
        "GERBIL_GXTEST",
        "GERBIL_LD",
        "GERBIL_NATIVE_ABI",
        "GERBIL_SDKROOT",
        "LDFLAGS",
        "LIBRARY_PATH",
        "PATH",
        "PKG_CONFIG_PATH",
    ],
    local = True,
)
