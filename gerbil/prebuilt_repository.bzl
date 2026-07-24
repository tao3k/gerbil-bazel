"""Repository rule for importing an immutable Gerbil toolchain capability."""

load(":gambit_runtime.bzl", "normalized_gambit_runtime")
load(
    ":host_system.bzl",
    "resolve_gerbil_build_cores",
    "resolve_host_environment",
    "stable_action_environment",
)

_ARCH_ALIASES = {
    "aarch64": "aarch64",
    "amd64": "x86_64",
    "arm64": "aarch64",
    "x86_64": "x86_64",
}

_ARCH_CONSTRAINTS = {
    "aarch64": "@platforms//cpu:aarch64",
    "x86_64": "@platforms//cpu:x86_64",
}

_OS_CONSTRAINTS = {
    "darwin": "@platforms//os:macos",
    "linux": "@platforms//os:linux",
}

_REQUIRED_TOOLS = ["gxc", "gxi", "gxpkg", "gxtest"]
_MANIFEST_SCHEMA = "gerbil-bazel.prebuilt-capability-manifest.v1"

def _shell_quote(value):
    return "'{}'".format(value.replace("'", "'\"'\"'"))

def _environment_exports(environment):
    return "\n".join([
        "export {}={}".format(key, _shell_quote(environment[key]))
        for key in sorted(environment.keys())
    ])

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
    entries = [
        "        {}: {},".format(repr(key), repr(environment[key]))
        for key in sorted(environment.keys())
    ]
    if not entries:
        return "{}"
    return "{\n" + "\n".join(entries) + "\n    }"

def _string_list(values):
    return "[{}]".format(", ".join([repr(value) for value in values]))

def _require_type(value, expected, description):
    if type(value) != expected:
        fail("{} must be {}, got {}".format(description, expected, type(value)))
    return value

def _require_string(mapping, key, description):
    value = _require_type(mapping.get(key), "string", description)
    if not value:
        fail("{} must not be empty".format(description))
    return value

def _safe_relative_path(value, description):
    value = _require_type(value, "string", description)
    if not value or value.startswith("/"):
        fail("{} must be a non-empty relative path".format(description))
    for segment in value.split("/"):
        if segment in ["", ".", ".."]:
            fail("{} contains an unsafe path segment: {}".format(description, value))
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
    if not dependency_state:
        return "declared-roots"
    if repository_ctx.attr.project_dependency_packages:
        return "project-dependency-override"
    return "project-package-manifest"

def _hex_digest(value, length, description):
    value = _require_type(value, "string", description).lower()
    if len(value) != length:
        fail("{} must contain {} hexadecimal characters".format(description, length))
    for character in value.elems():
        if character not in "0123456789abcdef":
            fail("{} must be hexadecimal".format(description))
    return value

def _normalized_arch(value):
    normalized = _ARCH_ALIASES.get(value.lower())
    if not normalized:
        fail("unsupported Gerbil capability architecture: {}".format(value))
    return normalized

def _manifest(repository_ctx):
    path = repository_ctx.path("payload/{}".format(
        _safe_relative_path(repository_ctx.attr.manifest_path, "manifest_path"),
    ))
    if not path.exists:
        fail("Gerbil capability manifest was not found: {}".format(path))
    manifest = _require_type(
        json.decode(repository_ctx.read(path)),
        "dict",
        "Gerbil capability manifest",
    )
    schema = _require_string(manifest, "schema", "manifest schema")
    if schema != _MANIFEST_SCHEMA:
        fail("unsupported Gerbil capability manifest schema: {}".format(schema))
    return manifest

def _payload_path(repository_ctx, relative, description):
    relative = _safe_relative_path(relative, description)
    path = repository_ctx.path("payload/{}".format(relative))
    if not path.exists:
        fail("{} does not exist in the Gerbil capability: {}".format(description, relative))
    return path

def _platform(repository_ctx, manifest, host):
    platform = _require_type(manifest.get("platform"), "dict", "manifest platform")
    system = _require_string(platform, "os", "manifest platform.os").lower()
    architecture = _normalized_arch(
        _require_string(platform, "arch", "manifest platform.arch"),
    )
    host_architecture = _normalized_arch(repository_ctx.os.arch)
    if system != host.system or architecture != host_architecture:
        fail(
            "Gerbil capability platform {}-{} does not match host {}-{}".format(
                system,
                architecture,
                host.system,
                host_architecture,
            ),
        )
    if system not in _OS_CONSTRAINTS:
        fail("unsupported Gerbil capability operating system: {}".format(system))
    return struct(
        architecture = architecture,
        constraints = [
            _OS_CONSTRAINTS[system],
            _ARCH_CONSTRAINTS[architecture],
        ],
        system = system,
    )

def _tool_paths(repository_ctx, manifest):
    declared = _require_type(manifest.get("tools"), "dict", "manifest tools")
    tools = {}
    relative_tools = {}
    for name in _REQUIRED_TOOLS:
        relative = _safe_relative_path(
            declared.get(name),
            "manifest tools.{}".format(name),
        )
        tools[name] = str(_payload_path(
            repository_ctx,
            relative,
            "Gerbil {} tool".format(name),
        ))
        relative_tools[name] = relative
    return struct(absolute = tools, relative = relative_tools)

def _version(repository_ctx, manifest, tools, environment):
    declared = _require_string(manifest, "version", "manifest version")
    result = repository_ctx.execute(
        [tools["gxi"], "--version"],
        environment = environment,
        quiet = True,
    )
    if result.return_code != 0:
        fail("prebuilt Gerbil version probe failed: {}".format(result.stderr.strip()))
    observed = result.stdout.strip()
    if observed != declared:
        fail("prebuilt Gerbil version mismatch: manifest={!r}, observed={!r}".format(
            declared,
            observed,
        ))
    expected = repository_ctx.attr.expected_version_prefixes
    if expected:
        accepted = False
        for prefix in expected:
            if observed.startswith("Gerbil v" + prefix) or observed.startswith(prefix):
                accepted = True
                break
        if not accepted:
            fail("Gerbil version {!r} does not match accepted prefixes {}".format(
                observed,
                expected,
            ))
    return observed

def _link_dependency_roots(repository_ctx, manifest):
    declared = _require_type(
        manifest.get("dependencyRoots"),
        "list",
        "manifest dependencyRoots",
    )
    if not declared:
        fail("manifest dependencyRoots must not be empty")
    repository_ctx.file("lib/.root", "gerbil-bazel prebuilt dependency root\n")
    relative_roots = []
    for index, relative in enumerate(declared):
        relative = _safe_relative_path(
            relative,
            "manifest dependencyRoots[{}]".format(index),
        )
        repository_ctx.symlink(
            _payload_path(
                repository_ctx,
                relative,
                "Gerbil dependency root",
            ),
            "lib/capability-{}".format(index),
        )
        relative_roots.append(relative)
    return relative_roots

def _link_project_dependencies(repository_ctx):
    packages = _project_dependency_packages(repository_ctx)
    if not packages:
        return {}
    if not repository_ctx.attr.project_root_marker:
        fail("project_root_marker is required when project dependency packages are declared")

    project_root = repository_ctx.path(repository_ctx.attr.project_root_marker).dirname
    library_relative = _safe_relative_path(
        repository_ctx.attr.project_library_relative_path,
        "project_library_relative_path",
    )
    library_root = repository_ctx.path("{}/{}".format(project_root, library_relative))
    state = {}
    linked = {}
    for package in packages:
        package = _safe_relative_path(package, "project dependency package")
        if package in state:
            fail("duplicate project dependency package: {}".format(package))
        dependency = repository_ctx.path("{}/{}".format(library_root, package))
        repository_ctx.watch(dependency)
        if dependency.exists:
            repository_ctx.watch_tree(dependency)
            link_name = package.split("/")[0]
            if link_name not in linked:
                link_root = repository_ctx.path("{}/{}".format(library_root, link_name))
                repository_ctx.symlink(link_root, "lib/{}".format(link_name))
                linked[link_name] = True
            state[package] = "ready"
        else:
            state[package] = "missing"
    return state

def _tool_rules():
    return "\n\n".join([
        """sh_binary(
    name = {name},
    srcs = [{wrapper}],
    data = [{raw}, "native_abi.txt"],
)""".format(
            name = repr(name),
            raw = repr("bin/{}_raw".format(name)),
            wrapper = repr("{}.sh".format(name)),
        )
        for name in sorted(_REQUIRED_TOOLS)
    ])

def _prebuilt_gerbil_repository_impl(repository_ctx):
    if not repository_ctx.attr.urls:
        fail("prebuilt Gerbil capability requires at least one URL")
    archive_sha256 = _hex_digest(
        repository_ctx.attr.sha256,
        64,
        "prebuilt archive sha256",
    )
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.urls,
        output = "payload",
        sha256 = archive_sha256,
        stripPrefix = repository_ctx.attr.strip_prefix,
        canonical_id = archive_sha256,
    )

    manifest = _manifest(repository_ctx)
    expected_install_digest = _hex_digest(
        repository_ctx.attr.install_digest,
        64,
        "expected install digest",
    )
    install_digest = _hex_digest(
        manifest.get("installDigest"),
        64,
        "manifest installDigest",
    )
    if install_digest != expected_install_digest:
        fail("Gerbil capability install digest mismatch: expected {}, manifest declares {}".format(
            expected_install_digest,
            install_digest,
        ))
    host = resolve_host_environment(
        repository_ctx,
        darwin_homebrew_formulae = repository_ctx.attr.darwin_homebrew_formulae,
    )
    platform = _platform(repository_ctx, manifest, host)
    tools = _tool_paths(repository_ctx, manifest)
    gerbil_home_relative = _safe_relative_path(
        manifest.get("gerbilHome"),
        "manifest gerbilHome",
    )
    gerbil_home = str(_payload_path(
        repository_ctx,
        gerbil_home_relative,
        "Gerbil home",
    ))
    native_abi = _hex_digest(
        manifest.get("nativeAbiFingerprint"),
        40,
        "manifest nativeAbiFingerprint",
    )
    capability_id = _require_string(manifest, "capabilityId", "manifest capabilityId")
    manifest_environment = _require_type(
        manifest.get("environment", {}),
        "dict",
        "manifest environment",
    )
    repository_environment = dict(manifest_environment)
    repository_environment.update(repository_ctx.attr.environment)
    environment = dict(host.environment)
    environment.update(repository_environment)
    runtime = normalized_gambit_runtime(
        repository_ctx,
        gerbil_home,
        host.gerbil_cc,
        environment,
        gambit_dynamic_link_options = host.gambit_dynamic_link_options,
        gambit_executable_linker = host.gerbil_cc if host.system == "darwin" else "",
    )
    build_cores = resolve_gerbil_build_cores(
        repository_ctx,
        repository_environment,
        host.system_cpu_count,
    )
    environment = stable_action_environment(
        runtime.environment,
        repository_environment,
    )
    tool_directory = str(repository_ctx.path(tools.absolute["gxi"]).dirname)
    inherited_path = environment.get(
        "PATH",
        repository_ctx.os.environ.get("PATH", ""),
    )
    environment["PATH"] = tool_directory + (":" + inherited_path if inherited_path else "")
    for name in ["AR", "CXX"]:
        value = repository_ctx.os.environ.get(name, "")
        if value:
            environment[name] = value

    version = _version(repository_ctx, manifest, tools.absolute, environment)
    dependency_roots = _link_dependency_roots(repository_ctx, manifest)
    project_dependency_state = _link_project_dependencies(repository_ctx)
    dependency_policy = _project_dependency_policy(repository_ctx, project_dependency_state)
    substitutions = {
        "{{ENVIRONMENT}}": _environment_exports(environment),
        "{{GXI}}": _shell_quote(tools.absolute["gxi"]),
        "{{GXPKG}}": _shell_quote(tools.absolute["gxpkg"]),
        "{{GXPKG_SCHEME}}": "#f",
        "{{NATIVE_ABI}}": _shell_quote(native_abi),
        "{{NATIVE_ENVIRONMENT_ARGS}}": _environment_args(environment),
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
    for name, path in tools.absolute.items():
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

    repository_ctx.file("native_abi.txt", native_abi + "\n")
    repository_ctx.file(
        "toolchain.receipt.json",
        json.encode_indent({
            "archiveSha256": archive_sha256,
            "capabilityId": capability_id,
            "dependencyPolicy": dependency_policy,
            "dependencyRoots": dependency_roots,
            "dependencyState": project_dependency_state,
            "environment": environment,
            "gerbilBuildCores": int(build_cores.value),
            "gerbilBuildCoresSource": build_cores.source,
            "gerbilHome": gerbil_home_relative,
            "gambitDynamicLinkOptions": host.gambit_dynamic_link_options,
            "gambitProducerOptions": {
                "dynamic": runtime.producer_dynamic_options,
                "object": runtime.producer_object_options,
            },
            "gerbilExecutableLinker": runtime.executable_linker,
            "installDigest": install_digest,
            "nativeAbiFingerprint": native_abi,
            "platform": {
                "arch": platform.architecture,
                "os": platform.system,
            },
            "producerCompilerCommand": runtime.compiler_command,
            "schema": "gerbil-bazel.prebuilt-toolchain-receipt.v1",
            "sourceUrls": repository_ctx.attr.urls,
            "systemCpuCount": int(host.system_cpu_count),
            "systemMemoryBytes": int(host.system_memory_bytes),
            "tools": tools.relative,
            "version": version,
        }, indent = "  ") + "\n",
    )
    repository_ctx.template(
        "BUILD.bazel",
        repository_ctx.attr._build_template,
        {
            "{{ENVIRONMENT_DICT}}": _environment_dict(environment),
            "{{EXEC_CONSTRAINTS}}": _string_list(platform.constraints),
            "{{GERBIL_AS}}": repr(host.gerbil_as),
            "{{GERBIL_CC}}": repr("gerbil-cc"),
            "{{GERBIL_GCC}}": repr("gerbil-gcc"),
            "{{GERBIL_LD}}": repr(host.gerbil_ld),
            "{{NATIVE_ABI}}": repr(native_abi),
            "{{SYSTEM_CPU_COUNT}}": repr(host.system_cpu_count),
            "{{SYSTEM_MEMORY_BYTES}}": repr(host.system_memory_bytes),
            "{{TOOL_RULES}}": _tool_rules(),
        },
    )

prebuilt_gerbil_repository = repository_rule(
    implementation = _prebuilt_gerbil_repository_impl,
    attrs = {
        "darwin_homebrew_formulae": attr.string_list(default = [
            "openssl@3",
            "sqlite",
            "zlib",
        ]),
        "environment": attr.string_dict(),
        "expected_version_prefixes": attr.string_list(),
        "install_digest": attr.string(mandatory = True),
        "manifest_path": attr.string(default = "gerbil-bazel-capability.json"),
        "project_dependency_packages": attr.string_list(),
        "project_library_relative_path": attr.string(default = ".gerbil/lib"),
        "project_root_marker": attr.label(allow_single_file = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(),
        "urls": attr.string_list(mandatory = True),
        "_build_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:prebuilt_toolchain.BUILD.bazel.tpl",
        ),
        "_install_dependencies_template": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:install_gerbil_dependencies.ss.tpl",
        ),
        "_functional": attr.label(
            default = "//gerbil:functional.ss",
            allow_single_file = True,
        ),
        "_resource_policy": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:resource_policy.ss",
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
    configure = True,
    environ = [
        "AR",
        "CC",
        "CPATH",
        "CXX",
        "GAMBOPT",
        "GERBIL_AS",
        "GERBIL_BUILD_CORES",
        "GERBIL_CC",
        "GERBIL_DEVELOPER_DIR",
        "GERBIL_LD",
        "GERBIL_SDKROOT",
        "LDFLAGS",
        "LIBRARY_PATH",
        "PATH",
        "PKG_CONFIG_PATH",
    ],
)
