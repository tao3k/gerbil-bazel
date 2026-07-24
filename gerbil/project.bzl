"""Generic Bazel rules for projects whose build truth is a Gerbil script."""

load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

GerbilProjectInfo = provider(
    doc = "Outputs of a Gerbil project build.",
    fields = {
        "dependency_roots": "transitive depset of isolated dependency project roots",
        "log": "complete project build log",
        "project_root": "tree artifact containing the isolated built project",
        "receipt": "machine-readable build receipt",
        "source_root_marker": "build script anchoring the declared project source root",
    },
)

def _staged_path(path):
    if path.startswith("../"):
        return ".gerbil-bazel/external/" + path[3:]
    if path.startswith(".gerbil-bazel/"):
        fail("project source path uses reserved staging namespace: {}".format(path))
    return path

def _source_entries(files):
    sources_by_destination = {}
    for file in files:
        destination = _staged_path(file.short_path)
        previous = sources_by_destination.get(destination)
        if previous != None:
            fail("staged project source collision at {}: {} and {}".format(
                destination,
                previous,
                file.path,
            ))
        sources_by_destination[destination] = file.path
    return [
        {
            "destination": destination,
            "source": sources_by_destination[destination],
        }
        for destination in sorted(sources_by_destination.keys())
    ]

def _gerbil_project_compile_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    project_dependencies = [dep[GerbilProjectInfo] for dep in ctx.attr.deps]
    dependency_roots = depset(
        direct = [dependency.project_root for dependency in project_dependencies],
        order = "postorder",
        transitive = [dependency.dependency_roots for dependency in project_dependencies],
    )
    project_root = ctx.actions.declare_directory(ctx.label.name + ".project")
    receipt = ctx.actions.declare_file(ctx.label.name + ".receipt.json")
    log = ctx.actions.declare_file(ctx.label.name + ".log")
    request = ctx.actions.declare_file(ctx.label.name + ".request.json")
    sources = depset(direct = [ctx.file.build_script] + ctx.files.srcs)
    ctx.actions.write(
        output = request,
        content = json.encode({
            "args": ctx.attr.args,
            "buildScript": _staged_path(ctx.file.build_script.short_path),
            "dependencyRootMarker": toolchain.dependency_library_root.path,
            "log": log.path,
            "packageIdentity": "",
            "packageRevision": "",
            "processGuard": ctx.attr.process_guard,
            "processGuardTimeoutSeconds": ctx.attr.process_guard_timeout_seconds,
            "projectDependencyRoots": [
                root.path
                for root in dependency_roots.to_list()
            ],
            "projectLabel": str(ctx.label),
            "projectRoot": project_root.path,
            "receipt": receipt.path,
            "receiptLinePrefix": ctx.attr.receipt_line_prefix,
            "requireLibraryOutput": ctx.attr.require_library_output,
            "schema": "gerbil-bazel.project-request.v1",
            "sources": _source_entries(sources.to_list()),
            "tools": {
                "as": toolchain.gerbil_as,
                "cc": toolchain.gerbil_cc,
                "gxc": toolchain.gxc.executable.path,
                "gxi": toolchain.gxi.executable.path,
                "gxpkg": toolchain.gxpkg.executable.path,
                "ld": toolchain.gerbil_ld,
            },
        }) + "\n",
    )
    args = ctx.actions.args()
    args.add(ctx.file._runner.path)
    args.add(request.path)
    environment = dict(toolchain.environment)
    environment.update(ctx.attr.env)
    environment["CC"] = toolchain.gerbil_cc
    environment["GERBIL_BAZEL_NATIVE_ABI"] = toolchain.native_abi_fingerprint
    ctx.actions.run(
        arguments = [args],
        env = environment,
        executable = toolchain.gxi,
        inputs = depset(
            direct = [
            ctx.file._functional,
            ctx.file._resource_policy,
                ctx.file._runner,
                request,
                toolchain.dependency_library_root,
                toolchain.native_abi_fingerprint_file,
            ],
            transitive = [
                sources,
                dependency_roots,
                toolchain.dependency_libraries,
                toolchain.compile_runfiles,
            ],
        ),
        mnemonic = "GerbilProjectCompile",
        outputs = [project_root, receipt, log],
        progress_message = "Building Gerbil project %{label}",
        tools = [
            toolchain.gxi,
            toolchain.gxc,
            toolchain.gxpkg,
        ],
    )
    info = GerbilProjectInfo(
        dependency_roots = dependency_roots,
        log = log,
        project_root = project_root,
        receipt = receipt,
        source_root_marker = ctx.file.build_script,
    )
    return [
        DefaultInfo(files = depset([project_root, receipt, log])),
        info,
        OutputGroupInfo(
            log = depset([log]),
            project_root = depset([project_root]),
            receipt = depset([receipt]),
        ),
    ]

gerbil_project_compile = rule(
    implementation = _gerbil_project_compile_impl,
    attrs = {
        "args": attr.string_list(),
        "build_script": attr.label(allow_single_file = True, mandatory = True),
        "deps": attr.label_list(providers = [GerbilProjectInfo]),
        "env": attr.string_dict(),
        "process_guard": attr.bool(default = False),
        "process_guard_timeout_seconds": attr.int(default = 0),
        "receipt_line_prefix": attr.string(),
        "require_library_output": attr.bool(default = False),
        "srcs": attr.label_list(allow_files = True),
        "_runner": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:project_runner.ss",
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
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def _runfile_key(ctx, file):
    if file.short_path.startswith("../"):
        return file.short_path[3:]
    return "{}/{}".format(ctx.workspace_name, file.short_path)

def _runfiles_init():
    return """rlocation() {
  local key=$1
  local runfiles_dir=${RUNFILES_DIR:-${BASH_SOURCE[0]}.runfiles}
  local runfiles_manifest=${RUNFILES_MANIFEST_FILE:-${BASH_SOURCE[0]}.runfiles_manifest}
  if [[ -e $runfiles_dir/$key ]]; then
    printf '%s\\n' "$runfiles_dir/$key"
    return
  fi
  if [[ -f $runfiles_manifest ]]; then
    awk -v key="$key" '$1 == key {sub($1 " ", ""); print; exit}' "$runfiles_manifest"
    return
  fi
  printf 'cannot resolve runfile: %s\\n' "$key" >&2
  exit 1
}
"""

def _gerbil_project_dev_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    executable = ctx.actions.declare_file(ctx.label.name)
    args = " ".join([repr(arg) for arg in ctx.attr.build_args])
    native_env_key = _runfile_key(ctx, toolchain.native_scheme_env.executable)
    dependency_root_key = _runfile_key(ctx, toolchain.dependency_library_root)
    project_dependencies = [dep[GerbilProjectInfo] for dep in ctx.attr.deps]
    dependency_roots = depset(
        direct = [dependency.project_root for dependency in project_dependencies],
        order = "postorder",
        transitive = [dependency.dependency_roots for dependency in project_dependencies],
    )
    project_dependency_keys = " ".join([
        repr(_runfile_key(ctx, root))
        for root in dependency_roots.to_list()
    ])
    test_files = ctx.files.test_files
    if test_files:
        command = """"$native_env" env GERBIL_PATH="$GERBIL_PATH" GERBIL_LOADPATH="$GERBIL_LOADPATH" "$gxi" "$workspace/{build_script}" {args}
gxtest=$(rlocation {gxtest_key})
exec "$native_env" env GERBIL_PATH="$GERBIL_PATH" GERBIL_LOADPATH="$GERBIL_LOADPATH" "$gxtest" "$@" {tests}
""".format(
            args = args,
            build_script = ctx.file.build_script.short_path,
            gxtest_key = repr(_runfile_key(ctx, toolchain.gxtest.executable)),
            tests = " ".join([
                '"$workspace/{}"'.format(file.short_path)
                for file in test_files
            ]),
        )
    else:
        command = 'exec "$native_env" env GERBIL_PATH="$GERBIL_PATH" GERBIL_LOADPATH="$GERBIL_LOADPATH" "$gxi" "$workspace/{}" {} "$@"\n'.format(
            ctx.file.build_script.short_path,
            args,
        )
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_init}
workspace=${{BUILD_WORKSPACE_DIRECTORY:?run this target with bazel run}}
gxi=$(rlocation {gxi_key})
native_env=$(rlocation {native_env_key})
dependency_root_marker=$(rlocation {dependency_root_key})
dependency_root=$(dirname "$dependency_root_marker")
project_dependency_loadpath=
for key in {project_dependency_keys}; do
  dependency_project_root=$(rlocation "$key")
  project_dependency_loadpath="$project_dependency_loadpath:$dependency_project_root/.gerbil/lib"
done
export GERBIL_PATH="$workspace/.gerbil"
export GERBIL_LOADPATH="$GERBIL_PATH/lib$project_dependency_loadpath:$dependency_root"
{command}
""".format(
            command = command,
            dependency_root_key = repr(dependency_root_key),
            gxi_key = repr(_runfile_key(ctx, toolchain.gxi.executable)),
            native_env_key = repr(native_env_key),
            project_dependency_keys = project_dependency_keys,
            runfiles_init = _runfiles_init(),
        ),
    )
    runfiles = ctx.runfiles(
        files = [
            ctx.file.build_script,
            toolchain.dependency_library_root,
            toolchain.gxtest.executable,
            toolchain.native_scheme_env.executable,
        ] + test_files,
        transitive_files = depset(transitive = [dependency_roots, toolchain.runfiles]),
    )
    return [DefaultInfo(executable = executable, runfiles = runfiles)]

_gerbil_project_dev = rule(
    implementation = _gerbil_project_dev_impl,
    attrs = {
        "build_args": attr.string_list(),
        "build_script": attr.label(allow_single_file = True, mandatory = True),
        "deps": attr.label_list(providers = [GerbilProjectInfo]),
        "test_files": attr.label_list(allow_files = True),
    },
    executable = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def gerbil_project_dev(name, build_script, args = [], deps = [], tests = [], **kwargs):
    """Declares a source-workspace development launcher for =bazel run=."""
    _gerbil_project_dev(
        name = name,
        build_args = args,
        build_script = build_script,
        deps = deps,
        test_files = tests,
        **kwargs
    )

def _gerbil_project_test_impl(ctx):
    project = ctx.attr.project[GerbilProjectInfo]
    toolchain = resolved_gerbil_toolchain(ctx)
    executable = ctx.actions.declare_file(ctx.label.name)
    project_key = _runfile_key(ctx, project.project_root)
    gxtest_key = _runfile_key(ctx, toolchain.gxtest.executable)
    native_env_key = _runfile_key(ctx, toolchain.native_scheme_env.executable)
    dependency_root_key = _runfile_key(ctx, toolchain.dependency_library_root)
    source_root_marker = ctx.file.source_root_marker or project.source_root_marker
    source_root_key = _runfile_key(ctx, source_root_marker)
    project_dependency_keys = " ".join([
        repr(_runfile_key(ctx, root))
        for root in project.dependency_roots.to_list()
    ])
    test_keys = " ".join([
        repr(_runfile_key(ctx, test_file))
        for test_file in ctx.files.test_files
    ])
    test_args = " ".join([repr(arg) for arg in ctx.attr.test_args])
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_init}
project_root=$(rlocation {project_key})
gxtest=$(rlocation {gxtest_key})
native_env=$(rlocation {native_env_key})
dependency_root_marker=$(rlocation {dependency_root_key})
dependency_root=$(dirname "$dependency_root_marker")
source_root_marker=$(rlocation {source_root_key})
source_root=$(dirname "$source_root_marker")
project_dependency_loadpath=
for key in {project_dependency_keys}; do
  dependency_project_root=$(rlocation "$key")
  project_dependency_loadpath="$project_dependency_loadpath:$dependency_project_root/.gerbil/lib"
done
test_files=()
for key in {test_keys}; do
  test_files+=("$(rlocation "$key")")
done
export GERBIL_PATH="$project_root/.gerbil"
export GERBIL_LOADPATH="$GERBIL_PATH/lib$project_dependency_loadpath:$source_root:$dependency_root"
cd "$source_root"
exec "$native_env" env GERBIL_PATH="$GERBIL_PATH" GERBIL_LOADPATH="$GERBIL_LOADPATH" "$gxtest" {test_args} "${{test_files[@]}}"
""".format(
            dependency_root_key = repr(dependency_root_key),
            gxtest_key = repr(gxtest_key),
            native_env_key = repr(native_env_key),
            project_key = repr(project_key),
            project_dependency_keys = project_dependency_keys,
            runfiles_init = _runfiles_init(),
            source_root_key = repr(source_root_key),
            test_args = test_args,
            test_keys = test_keys,
        ),
    )
    transitive_files = [project.dependency_roots, toolchain.runfiles]
    for srcs in ctx.attr.srcs:
        transitive_files.append(srcs[DefaultInfo].files)
    runfile_files = [
        project.project_root,
        project.receipt,
        source_root_marker,
        toolchain.dependency_library_root,
        toolchain.gxtest.executable,
        toolchain.native_scheme_env.executable,
    ]
    return [DefaultInfo(
        executable = executable,
        runfiles = ctx.runfiles(
            files = runfile_files + ctx.files.test_files,
            transitive_files = depset(transitive = transitive_files),
        ),
    )]

_gerbil_project_test = rule(
    implementation = _gerbil_project_test_impl,
    attrs = {
        "project": attr.label(mandatory = True, providers = [GerbilProjectInfo]),
        "source_root_marker": attr.label(allow_single_file = True),
        "srcs": attr.label_list(allow_files = True),
        "test_args": attr.string_list(),
        "test_files": attr.label_list(allow_files = True, mandatory = True),
    },
    test = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def _normalize_test_label(value):
    if type(value) != "string":
        return value
    if value.startswith("@") or value.startswith("//") or value.startswith(":"):
        return value
    package = native.package_name()
    package_prefix = package + "/" if package else ""
    if package_prefix and value.startswith(package_prefix):
        return ":" + value[len(package_prefix):]
    return value

def gerbil_project_test(
        name,
        project,
        tests,
        source_root_marker = None,
        srcs = [],
        test_args = [],
        **kwargs):
    """Executes tests against one explicit GerbilProjectInfo build."""
    if not tests:
        fail("gerbil_project_test requires at least one test file")
    declared_srcs = srcs if type(srcs) == "list" else [srcs]
    declared_tests = [_normalize_test_label(test) for test in tests]
    _gerbil_project_test(
        name = name,
        project = project,
        source_root_marker = source_root_marker,
        srcs = declared_srcs,
        test_args = test_args,
        test_files = declared_tests,
        **kwargs
    )
