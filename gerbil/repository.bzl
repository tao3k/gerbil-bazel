"""Repository rule for discovering a native Gerbil installation."""

load(
    ":gambit_runtime.bzl",
    "discover_gambit_compiler_command",
    "discover_gambit_home",
    "normalized_gambit_runtime",
)
load(
    ":host_system.bzl",
    "resolve_gerbil_build_cores",
    "resolve_host_environment",
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

def _safe_relative_path(value, field):
    if not value or value.startswith("/") or value == ".." or value.startswith("../") or "/../" in value or value.endswith("/.."):
        fail("{} must be a non-empty relative path without parent traversal: {}".format(field, value))
    return value

def _quoted_strings(value):
    strings = []
    parts = value.split("\"")
    if len(parts) % 2 == 0:
        fail("unterminated quoted string in Gerbil package manifest")
    for index, part in enumerate(parts):
        if index % 2 == 1:
            strings.append(part)
    return strings

def _dependency_repository_from_manifest_entry(dependency):
    revision_index = dependency.find("@")
    if revision_index < 0:
        return dependency
    return dependency[:revision_index]

def _package_name_from_manifest(manifest):
    package_index = manifest.find("package:")
    if package_index < 0:
        return ""
    tail = manifest[package_index + len("package:"):]
    tail = tail.replace("(", " ")
    tail = tail.replace(")", " ")
    tail = tail.replace("\n", " ")
    tail = tail.replace("\r", " ")
    tail = tail.replace("\t", " ")
    for field in tail.split(" "):
        if field:
            return field
    return ""

def _dependency_package_name(repository_ctx, project_root, dependency):
    repository = _dependency_repository_from_manifest_entry(dependency)
    package_manifest = repository_ctx.path("{}/.gerbil/pkg/{}/gerbil.pkg".format(
        project_root,
        repository,
    ))
    repository_ctx.watch(package_manifest)
    if package_manifest.exists:
        package = _package_name_from_manifest(repository_ctx.read(package_manifest))
        if package:
            return package
    return repository

def _project_dependency_packages(repository_ctx):
    if repository_ctx.attr.project_dependency_packages:
        return repository_ctx.attr.project_dependency_packages
    if repository_ctx.attr.project_root_marker == None:
        return []

    project_root = repository_ctx.path(repository_ctx.attr.project_root_marker).dirname
    manifest = repository_ctx.read(repository_ctx.attr.project_root_marker)
    depend_index = manifest.find("depend:")
    if depend_index < 0:
        return []
    policy_index = manifest.find("\n policy:", depend_index)
    if policy_index < 0:
        policy_index = len(manifest)
    packages = []
    seen = {}
    for dependency in _quoted_strings(manifest[depend_index:policy_index]):
        package = _dependency_package_name(repository_ctx, project_root, dependency)
        if package and package not in seen:
            packages.append(package)
            seen[package] = True
    return packages

def _project_dependency_policy(repository_ctx, dependency_state):
    if dependency_state:
        if repository_ctx.attr.project_dependency_packages:
            return "project-dependency-override"
        return "project-package-manifest"
    if repository_ctx.attr.dependency_roots:
        return "declared-roots"
    return "host-only"

def _link_dependency_roots(repository_ctx):
    repository_ctx.file("lib/.root", "gerbil-bazel dependency root\n")
    for index, root in enumerate(repository_ctx.attr.dependency_roots):
        path = repository_ctx.path(root)
        if not path.exists:
            fail("Gerbil dependency root does not exist: {}".format(root))
        repository_ctx.symlink(path, "lib/dependency-{}".format(index))

def _link_project_dependencies(repository_ctx):
    packages = _project_dependency_packages(repository_ctx)
    if not packages:
        return {}
    if repository_ctx.attr.project_root_marker == None:
        fail("project_root_marker is required when project dependency packages are set")

    relative_path = _safe_relative_path(
        repository_ctx.attr.project_library_relative_path,
        "project_library_relative_path",
    )
    project_root = repository_ctx.path(repository_ctx.attr.project_root_marker).dirname
    library_root = repository_ctx.path(str(project_root) + "/" + relative_path)
    state = {}
    names = {}
    linked = {}
    for package in packages:
        package = _safe_relative_path(package, "project dependency package")
        if package in names:
            fail("duplicate project dependency package: {}".format(package))
        names[package] = True
        dependency = repository_ctx.path(str(library_root) + "/" + package)
        repository_ctx.watch(dependency)
        if dependency.exists:
            repository_ctx.watch_tree(dependency)
            link_name = package.split("/")[0]
            if link_name not in linked:
                link_root = repository_ctx.path(str(library_root) + "/" + link_name)
                repository_ctx.symlink(link_root, "lib/" + link_name)
                linked[link_name] = True
            state[package] = "ready"
        else:
            state[package] = "missing"
    return state

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
    declared_environment = dict(host.environment)
    declared_environment.update(repository_ctx.attr.environment)
    runtime = normalized_gambit_runtime(
        repository_ctx,
        gambit_home,
        compiler_command,
        declared_environment,
        gambit_dynamic_link_options = host.gambit_dynamic_link_options,
        gambit_executable_linker = host.gerbil_cc if host.system == "darwin" else "",
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
    environment = runtime.environment
    environment["GERBIL_BUILD_CORES"] = build_cores.value
    environment["GERBIL_BAZEL_CPU_COUNT"] = host.system_cpu_count
    environment["GERBIL_BAZEL_MEMORY_BYTES"] = host.system_memory_bytes
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
        "{{NATIVE_ABI}}": _shell_quote(fingerprint),
        "{{NATIVE_ENVIRONMENT_ARGS}}": _environment_args(environment),
        "{{RESOURCE_GUARD}}": _shell_quote(str(repository_ctx.path(repository_ctx.attr._resource_guard))),
    }
    repository_ctx.template(
        "native_scheme_env.sh",
        repository_ctx.attr._native_scheme_env_template,
        substitutions,
        executable = True,
    )
    repository_ctx.template(
        "install_gerbil_dependencies.sh",
        repository_ctx.attr._install_dependencies_template,
        substitutions,
        executable = True,
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
    project_dependency_state = _link_project_dependencies(repository_ctx)
    repository_ctx.file("native_abi.txt", fingerprint + "\n")
    repository_ctx.file(
        "toolchain.receipt.json",
        json.encode_indent({
            "environment": environment,
            "dependencyPolicy": _project_dependency_policy(repository_ctx, project_dependency_state),
            "dependencyState": project_dependency_state,
            "gambitDynamicLinkOptions": host.gambit_dynamic_link_options,
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
        "project_dependency_packages": attr.string_list(),
        "project_library_relative_path": attr.string(default = ".gerbil/lib"),
        "project_root_marker": attr.label(allow_single_file = True),
        "tool_paths": attr.string_dict(),
        "_build_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:local_toolchain.BUILD.bazel.tpl",
        ),
        "_install_dependencies_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:install_gerbil_dependencies.sh.tpl",
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
        "_resource_guard": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:resource_guard.ss",
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
