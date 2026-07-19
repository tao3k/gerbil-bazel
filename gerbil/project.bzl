"""Generic Bazel rules for projects whose build truth is a Gerbil script."""

load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

GerbilProjectInfo = provider(
    doc = "Outputs of a Gerbil project build.",
    fields = {
        "log": "complete project build log",
        "project_root": "tree artifact containing the isolated built project",
        "receipt": "machine-readable build receipt",
    },
)

def _staged_path(path):
    if path.startswith("../"):
        return ".gerbil-bazel/external/" + path[3:]
    if path.startswith(".gerbil-bazel/"):
        fail("project source path uses reserved staging namespace: {}".format(path))
    return path

def _manifest_entries(files):
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
        "{}\t{}".format(sources_by_destination[destination], destination)
        for destination in sorted(sources_by_destination.keys())
    ]

def _gerbil_project_compile_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    project_root = ctx.actions.declare_directory(ctx.label.name + ".project")
    receipt = ctx.actions.declare_file(ctx.label.name + ".receipt.json")
    log = ctx.actions.declare_file(ctx.label.name + ".log")
    manifest = ctx.actions.declare_file(ctx.label.name + ".sources")
    sources = depset(direct = [ctx.file.build_script] + ctx.files.srcs)
    ctx.actions.write(
        output = manifest,
        content = "\n".join(_manifest_entries(sources.to_list())) + "\n",
    )
    args = ctx.actions.args()
    args.add(toolchain.gxi.executable.path)
    args.add(toolchain.gxc.executable.path)
    args.add(toolchain.gxpkg.executable.path)
    args.add(toolchain.gerbil_cc)
    args.add(toolchain.gerbil_as)
    args.add(toolchain.gerbil_ld)
    args.add(toolchain.dependency_library_root.path)
    args.add(manifest.path)
    args.add(project_root.path)
    args.add(_staged_path(ctx.file.build_script.short_path))
    args.add(receipt.path)
    args.add(log.path)
    args.add(ctx.attr.receipt_line_prefix)
    args.add(ctx.file._json_validator.path)
    args.add_all(ctx.attr.args)
    environment = dict(toolchain.environment)
    environment.update(ctx.attr.env)
    environment["GERBIL_BAZEL_NATIVE_ABI"] = toolchain.native_abi_fingerprint
    ctx.actions.run(
        arguments = [args],
        env = environment,
        executable = ctx.executable._runner,
        inputs = depset(
            direct = [
                ctx.file._json_validator,
                manifest,
                toolchain.dependency_library_root,
                toolchain.native_abi_fingerprint_file,
            ],
            transitive = [
                sources,
                toolchain.dependency_libraries,
                toolchain.runfiles,
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
        log = log,
        project_root = project_root,
        receipt = receipt,
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
        "env": attr.string_dict(),
        "receipt_line_prefix": attr.string(),
        "srcs": attr.label_list(allow_files = True),
        "_runner": attr.label(
            cfg = "exec",
            default = "@gerbil_bazel//gerbil:run_project",
            executable = True,
        ),
        "_json_validator": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:validate_json.ss",
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
export GERBIL_PATH="$workspace/.gerbil"
export GERBIL_LOADPATH="$GERBIL_PATH/lib:$dependency_root"
{command}
""".format(
            command = command,
            dependency_root_key = repr(dependency_root_key),
            gxi_key = repr(_runfile_key(ctx, toolchain.gxi.executable)),
            native_env_key = repr(native_env_key),
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
        transitive_files = toolchain.runfiles,
    )
    return [DefaultInfo(executable = executable, runfiles = runfiles)]

_gerbil_project_dev = rule(
    implementation = _gerbil_project_dev_impl,
    attrs = {
        "build_args": attr.string_list(),
        "build_script": attr.label(allow_single_file = True, mandatory = True),
        "test_files": attr.label_list(allow_files = True),
    },
    executable = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def gerbil_project_dev(name, build_script, args = [], tests = [], **kwargs):
    """Declares a source-workspace development launcher for =bazel run=."""
    _gerbil_project_dev(
        name = name,
        build_args = args,
        build_script = build_script,
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
    source_root_setup = ""
    source_root_suffix = ""
    if ctx.file.source_root_marker:
        source_root_setup = """source_root_marker=$(rlocation {})
source_root=$(dirname "$source_root_marker")
""".format(repr(_runfile_key(ctx, ctx.file.source_root_marker)))
        source_root_suffix = ":$source_root"
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
{source_root_setup}test_files=()
for key in {test_keys}; do
  test_files+=("$(rlocation "$key")")
done
export GERBIL_PATH="$project_root/.gerbil"
export GERBIL_LOADPATH="$GERBIL_PATH/lib{source_root_suffix}:$dependency_root"
cd "$project_root"
exec "$native_env" env GERBIL_PATH="$GERBIL_PATH" GERBIL_LOADPATH="$GERBIL_LOADPATH" "$gxtest" {test_args} "${{test_files[@]}}"
""".format(
            dependency_root_key = repr(dependency_root_key),
            gxtest_key = repr(gxtest_key),
            native_env_key = repr(native_env_key),
            project_key = repr(project_key),
            runfiles_init = _runfiles_init(),
            source_root_suffix = source_root_suffix,
            source_root_setup = source_root_setup,
            test_args = test_args,
            test_keys = test_keys,
        ),
    )
    transitive_files = [toolchain.runfiles]
    for srcs in ctx.attr.srcs:
        transitive_files.append(srcs[DefaultInfo].files)
    runfile_files = [
        project.project_root,
        project.receipt,
        toolchain.dependency_library_root,
        toolchain.gxtest.executable,
        toolchain.native_scheme_env.executable,
    ]
    if ctx.file.source_root_marker:
        runfile_files.append(ctx.file.source_root_marker)
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
