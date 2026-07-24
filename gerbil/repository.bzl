"""Repository rule for discovering a native Gerbil installation."""

load(
    ":gambit_runtime.bzl",
    "discover_gambit_compiler_command",
    "discover_gambit_home",
    "materialize_gambit_link_runtime",
    "normalized_gambit_runtime",
)
load(
    ":host_system.bzl",
    "relocatable_action_environment",
    "resolve_gerbil_build_cores",
    "resolve_host_environment",
    "stable_action_environment",
)

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

def _environment_args(environment):
    return " ".join([
        _shell_quote("{}={}".format(key, environment[key]))
        for key in sorted(environment.keys())
    ])

def _scheme_string(value):
    return json.encode(value)

def _scheme_environment_setters(environment):
    if not environment:
        return "  (void)"
    return "\n".join([
        "  (setenv {} {})".format(
            _scheme_string(key),
            _scheme_string(environment[key]),
        )
        for key in sorted(environment.keys())
    ])

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
    data = [
        {raw},
        \"gerbil-cc\",
        \"gerbil-gcc\",
        \"gerbil-gsc\",
        \"native_abi.txt\",
    ],
)""".format(
            name = repr(name),
            raw = repr("bin/{}_raw".format(name)),
            wrapper = repr("{}.sh".format(name)),
        ))
    return "\n\n".join(rules)

def _fingerprint(repository_ctx, host, tools, gerbil_cc, gerbil_cc_identity):
    override = repository_ctx.os.environ.get("GERBIL_NATIVE_ABI", "")
    if override:
        return override
    result = repository_ctx.execute(
        ["/usr/bin/env", "bash", str(repository_ctx.path(repository_ctx.attr._native_abi_probe))] + [
            tools["gxi"],
            tools["gxc"],
            tools["gxpkg"],
            tools["gxtest"],
            gerbil_cc,
            gerbil_cc_identity,
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
    gambit_home = discover_gambit_home(repository_ctx, tools["gxi"])
    compiler_command = host.gerbil_cc
    if not repository_ctx.os.environ.get("GERBIL_CC", ""):
        compiler_command = discover_gambit_compiler_command(repository_ctx, gambit_home)
    repository_environment = dict(repository_ctx.attr.environment)
    declared_environment = dict(host.environment)
    declared_environment.update(repository_environment)
    runtime = normalized_gambit_runtime(
        repository_ctx,
        gambit_home,
        compiler_command,
        declared_environment,
        gambit_dynamic_link_options = host.gambit_dynamic_link_options,
        gambit_executable_linker = host.gerbil_cc if host.system == "darwin" else "",
    )
    gambit_link_runtime = materialize_gambit_link_runtime(
        repository_ctx,
        gambit_home,
    )
    build_cores = resolve_gerbil_build_cores(
        repository_ctx,
        repository_ctx.attr.environment,
        host.system_cpu_count,
    )
    gerbil_cc = str(runtime.compiler_path)
    version = _gerbil_version(repository_ctx, tools)
    fingerprint = _fingerprint(
        repository_ctx,
        host,
        tools,
        gerbil_cc,
        str(runtime.compiler_identity_path),
    )
    environment = stable_action_environment(
        relocatable_action_environment(runtime.environment),
        repository_environment,
    )
    tool_directory = str(repository_ctx.path(tools["gxi"]).dirname)
    inherited_path = environment.get(
        "PATH",
        repository_ctx.os.environ.get("PATH", ""),
    )
    environment["PATH"] = tool_directory + (":" + inherited_path if inherited_path else "")
    if host.system == "linux":
        for name in ["AR", "CXX"]:
            value = repository_ctx.os.environ.get(name, "")
            if value:
                environment[name] = value

    substitutions = {
        "{{ENVIRONMENT}}": _environment_exports(environment),
        "{{GXI}}": _shell_quote(tools["gxi"]),
        "{{GXPKG}}": _shell_quote(tools["gxpkg"]),
        "{{GXPKG_SCHEME}}": "#f",
        "{{NATIVE_ABI}}": _shell_quote(fingerprint),
        "{{NATIVE_ENVIRONMENT_ARGS}}": _environment_args(environment),
        "{{RUNFILES_REPOSITORY}}": _shell_quote(repository_ctx.name),
        "{{ENVIRONMENT_SETTERS}}": _scheme_environment_setters(environment),
    }
    repository_ctx.template(
        "native_scheme_env.sh",
        repository_ctx.attr._native_scheme_env_template,
        substitutions,
        executable = True,
    )
    repository_ctx.template(
        "install_gerbil_dependencies.ss",
        repository_ctx.attr._install_dependencies_template,
        substitutions,
        executable = True,
    )
    repository_ctx.symlink(
        repository_ctx.path(repository_ctx.attr._functional),
        "functional.ss",
    )
    repository_ctx.symlink(
        repository_ctx.path(repository_ctx.attr._resource_policy),
        "resource_policy.ss",
    )

    for name, path in tools.items():
        repository_ctx.symlink(path, "bin/{}_raw".format(name))
        tool_substitutions = dict(substitutions)
        tool_substitutions["{{TOOL}}"] = _shell_quote(path)
        tool_substitutions["{{TOOL_NAME}}"] = _shell_quote(name)
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
            "gambitDynamicLinkOptions": host.gambit_dynamic_link_options,
            "gambitStaticLinkAvailable": gambit_link_runtime.available,
            "gambitProducerOptions": {
                "dynamic": runtime.producer_dynamic_options,
                "object": runtime.producer_object_options,
            },
            "gerbilExecutableLinker": runtime.executable_linker,
            "nativeAbiFingerprint": fingerprint,
            "producerCompilerCommand": runtime.compiler_command,
            "gerbilBuildCores": int(build_cores.value),
            "gerbilBuildCoresSource": build_cores.source,
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
            "{{GAMBIT_LINK_LIBRARIES}}": repr(host.gambit_link_libraries),
            "{{GAMBIT_LIBRARY_FILES}}": repr(gambit_link_runtime.files),
            "{{GAMBIT_STATIC_LINK_AVAILABLE}}": repr(gambit_link_runtime.available),
            "{{GERBIL_AS}}": repr(host.gerbil_as),
            "{{GERBIL_CC}}": repr("gerbil-cc"),
            "{{GERBIL_GCC}}": repr("gerbil-gcc"),
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
        "_install_dependencies_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:install_gerbil_dependencies.ss.tpl",
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
        "_functional": attr.label(
            default = "//gerbil:functional.ss",
            allow_single_file = True,
        ),
        "_resource_policy": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:resource_policy.ss",
        ),
    },
    environ = [
        "AR",
        "CC",
        "CPATH",
        "CXX",
        "GERBIL_AS",
        "GERBIL_BUILD_CORES",
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
