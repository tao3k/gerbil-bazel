"""Generic Bazel rules for projects whose build truth is a Gerbil script."""

load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

GerbilProjectInfo = provider(
    doc = "Outputs of a Gerbil project build.",
    fields = {
        "log": "complete build-script log",
        "project_root": "tree artifact containing the isolated built project",
        "receipt": "machine-readable build receipt",
    },
)

def _stage_relative_path(path):
    if path.startswith("../"):
        return "external/" + path[3:]
    return path

def _manifest_entry(file):
    return "{}\t{}".format(file.path, _stage_relative_path(file.short_path))

def _gerbil_project_compile_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    project_root = ctx.actions.declare_directory(ctx.label.name + ".project")
    receipt = ctx.actions.declare_file(ctx.label.name + ".receipt.json")
    log = ctx.actions.declare_file(ctx.label.name + ".log")
    manifest = ctx.actions.declare_file(ctx.label.name + ".sources")
    sources = depset(direct = [ctx.file.build_script] + ctx.files.srcs)
    ctx.actions.write(
        output = manifest,
        content = "\n".join([_manifest_entry(file) for file in sources.to_list()]) + "\n",
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
    args.add(_stage_relative_path(ctx.file.build_script.short_path))
    args.add(receipt.path)
    args.add(log.path)
    args.add(ctx.attr.receipt_line_prefix)
    args.add_all(ctx.attr.args)
    environment = dict(toolchain.environment)
    environment.update({
        "GERBIL_BAZEL_NATIVE_ABI": toolchain.native_abi_fingerprint,
        "GERBIL_BUILD_CORES": toolchain.system_cpu_count,
    })
    environment.update(ctx.attr.env)
    ctx.actions.run(
        arguments = [args],
        env = environment,
        executable = ctx.executable._runner,
        inputs = depset(
            direct = [
                manifest,
                toolchain.dependency_library_root,
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
        tools = [toolchain.gxi, toolchain.gxc, toolchain.gxpkg],
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
    test_commands = []
    for test_file in ctx.files.test_files:
        test_commands.append('"$gxtest" "$workspace/%s"' % test_file.short_path)
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_init}
workspace=${{BUILD_WORKSPACE_DIRECTORY:?run this target with bazel run}}
gxi=$(rlocation {gxi_key})
gxtest=$(rlocation {gxtest_key})
export PATH="$(dirname "$gxi"):$PATH"
"$gxi" "$workspace/{build_script}" {args} "$@"
{test_commands}
""".format(
            args = args,
            build_script = ctx.file.build_script.short_path,
            gxi_key = repr(_runfile_key(ctx, toolchain.gxi.executable)),
            gxtest_key = repr(_runfile_key(ctx, toolchain.gxtest.executable)),
            runfiles_init = _runfiles_init(),
            test_commands = "\n".join(test_commands),
        ),
    )
    runfiles = ctx.runfiles(
        files = [ctx.file.build_script] + ctx.files.test_files,
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
    dependency_root_key = _runfile_key(ctx, toolchain.dependency_library_root)
    gxi_key = _runfile_key(ctx, toolchain.gxi.executable)
    gxc_key = _runfile_key(ctx, toolchain.gxc.executable)
    gxpkg_key = _runfile_key(ctx, toolchain.gxpkg.executable)
    gxtest_key = _runfile_key(ctx, toolchain.gxtest.executable)
    tests = " ".join([
        '"$(rlocation %s)"' % repr(_runfile_key(ctx, test_file))
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
dependency_root_marker=$(rlocation {dependency_root_key})
dependency_root=$(dirname "$dependency_root_marker")
gxi=$(rlocation {gxi_key})
gxc=$(rlocation {gxc_key})
gxpkg=$(rlocation {gxpkg_key})
gxtest=$(rlocation {gxtest_key})
export GERBIL_PATH="$project_root/.gerbil"
export GERBIL_LOADPATH="$GERBIL_PATH/lib:$dependency_root:${{TEST_SRCDIR:?}}/${{TEST_WORKSPACE:?}}"
export PATH="$(dirname "$gxi"):$PATH"
cd "${{TEST_SRCDIR}}/${{TEST_WORKSPACE}}"
exec "$gxtest" {test_args} {tests}
""".format(
            dependency_root_key = repr(dependency_root_key),
            gxc_key = repr(gxc_key),
            gxi_key = repr(gxi_key),
            gxpkg_key = repr(gxpkg_key),
            gxtest_key = repr(gxtest_key),
            project_key = repr(project_key),
            runfiles_init = _runfiles_init(),
            test_args = test_args,
            tests = tests,
        ),
    )
    return [DefaultInfo(
        executable = executable,
        runfiles = ctx.runfiles(
            files = [
                toolchain.dependency_library_root,
                toolchain.gxc.executable,
                toolchain.gxi.executable,
                toolchain.gxpkg.executable,
                toolchain.gxtest.executable,
                project.log,
                project.project_root,
                project.receipt,
            ] + ctx.files.test_files,
            transitive_files = depset(
                transitive = [
                    ctx.attr.srcs[DefaultInfo].files,
                    toolchain.dependency_libraries,
                    toolchain.runfiles,
                ],
            ),
        ),
    )]

_gerbil_project_test = rule(
    implementation = _gerbil_project_test_impl,
    attrs = {
        "project": attr.label(mandatory = True, providers = [GerbilProjectInfo]),
        "srcs": attr.label(mandatory = True),
        "test_args": attr.string_list(),
        "test_files": attr.label_list(allow_files = True, mandatory = True),
    },
    test = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

gerbil_project_test = _gerbil_project_test
