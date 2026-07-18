"""Generic Bazel rules for projects whose build truth is a Gerbil script."""

load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

GerbilProjectInfo = provider(
    doc = "Outputs of a Gerbil project build.",
    fields = {
        "project_root": "tree artifact containing the isolated built project",
        "receipt": "machine-readable build receipt",
    },
)

def _strip_external_prefix(path):
    if path.startswith("../"):
        return path[3:]
    return path

def _manifest_entry(file):
    return "{}\t{}".format(file.path, _strip_external_prefix(file.short_path))

def _merged_environment(base, overrides):
    environment = dict(base)
    environment.update(overrides)
    return environment

def _gerbil_project_compile_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    project_root = ctx.actions.declare_directory(ctx.label.name + ".project")
    receipt = ctx.actions.declare_file(ctx.label.name + ".receipt.json")
    manifest = ctx.actions.declare_file(ctx.label.name + ".sources")
    sources = depset(direct = [ctx.file.build_script] + ctx.files.srcs)
    ctx.actions.write(
        output = manifest,
        content = "\n".join([_manifest_entry(file) for file in sources.to_list()]) + "\n",
    )
    args = ctx.actions.args()
    args.add(toolchain.gxi.executable.path)
    args.add(manifest.path)
    args.add(project_root.path)
    args.add(_strip_external_prefix(ctx.file.build_script.short_path))
    args.add(receipt.path)
    args.add_all(ctx.attr.args)
    ctx.actions.run(
        arguments = [args],
        env = _merged_environment(toolchain.environment, ctx.attr.env),
        executable = ctx.executable._runner,
        inputs = depset(
            direct = [manifest, toolchain.gxi.executable],
            transitive = [sources, toolchain.runfiles],
        ),
        mnemonic = "GerbilProjectCompile",
        outputs = [project_root, receipt],
        progress_message = "Building Gerbil project %{label}",
        tools = [toolchain.gxi],
    )
    info = GerbilProjectInfo(project_root = project_root, receipt = receipt)
    return [
        DefaultInfo(files = depset([project_root, receipt])),
        info,
    ]

gerbil_project_compile = rule(
    implementation = _gerbil_project_compile_impl,
    attrs = {
        "args": attr.string_list(),
        "build_script": attr.label(allow_single_file = True, mandatory = True),
        "env": attr.string_dict(),
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
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_init}
workspace=${{BUILD_WORKSPACE_DIRECTORY:?run this target with bazel run}}
gxi=$(rlocation {gxi_key})
exec "$gxi" "$workspace/{build_script}" {args} "$@"
""".format(
            args = args,
            build_script = ctx.file.build_script.short_path,
            gxi_key = repr(_runfile_key(ctx, toolchain.gxi.executable)),
            runfiles_init = _runfiles_init(),
        ),
    )
    runfiles = ctx.runfiles(
        files = [ctx.file.build_script],
        transitive_files = toolchain.runfiles,
    )
    return [DefaultInfo(executable = executable, runfiles = runfiles)]

_gerbil_project_dev = rule(
    implementation = _gerbil_project_dev_impl,
    attrs = {
        "build_args": attr.string_list(),
        "build_script": attr.label(allow_single_file = True, mandatory = True),
    },
    executable = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def gerbil_project_dev(name, build_script, args = [], **kwargs):
    """Declares a source-workspace development launcher for =bazel run=."""
    _gerbil_project_dev(
        name = name,
        build_args = args,
        build_script = build_script,
        **kwargs
    )

def _gerbil_project_test_impl(ctx):
    project = ctx.attr.project[GerbilProjectInfo]
    toolchain = resolved_gerbil_toolchain(ctx)
    executable = ctx.actions.declare_file(ctx.label.name)
    project_key = _runfile_key(ctx, project.project_root)
    gxtest_key = _runfile_key(ctx, toolchain.gxtest.executable)
    tests = " ".join([repr(test) for test in ctx.attr.test_files])
    test_args = " ".join([repr(arg) for arg in ctx.attr.test_args])
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_init}
project_root=$(rlocation {project_key})
gxtest=$(rlocation {gxtest_key})
export GERBIL_PATH="$project_root/.gerbil"
cd "$project_root"
exec "$gxtest" {test_args} {tests}
""".format(
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
                project.project_root,
                project.receipt,
                toolchain.gxtest.executable,
            ],
            transitive_files = toolchain.runfiles,
        ),
    )]

_gerbil_project_test = rule(
    implementation = _gerbil_project_test_impl,
    attrs = {
        "project": attr.label(mandatory = True, providers = [GerbilProjectInfo]),
        "test_args": attr.string_list(),
        "test_files": attr.string_list(mandatory = True),
    },
    test = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)

def gerbil_project_test(
        name,
        build_script,
        tests,
        srcs = [],
        build_args = ["compile"],
        test_args = [],
        **kwargs):
    """Builds a Gerbil project, then executes its test files with gxtest."""
    compile_name = name + "_compile"
    gerbil_project_compile(
        name = compile_name,
        args = build_args,
        build_script = build_script,
        srcs = srcs,
        testonly = True,
        visibility = ["//visibility:private"],
    )
    _gerbil_project_test(
        name = name,
        project = ":" + compile_name,
        test_args = test_args,
        test_files = tests,
        **kwargs
    )
