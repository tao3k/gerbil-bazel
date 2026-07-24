"""Lifecycle-safe public test rule for built Gerbil packages."""

load(":providers.bzl", "GerbilPackageInfo")
load(
    ":runfiles.bzl",
    "environment_exports",
    "quoted_runfile_keys",
    "runfile_key",
    "runfiles_resolver",
    "shell_quote",
)
load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

def _gerbil_test_impl(ctx):
    if not ctx.files.tests:
        fail("{} requires at least one test file".format(ctx.label))

    package = ctx.attr.package[GerbilPackageInfo]
    toolchain = resolved_gerbil_toolchain(ctx)
    executable = ctx.actions.declare_file(ctx.label.name)
    dependency_roots = package.dependency_roots.to_list()

    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_resolver}
package_root=$(rlocation {package_key})
gxtest=$(rlocation {gxtest_key})
dependency_root_marker=$(rlocation {dependency_root_key})
dependency_library_root=$(dirname "$dependency_root_marker")
loadpath=("$package_root/.gerbil/lib")
for key in {dependency_keys}; do
  dependency_package_root=$(rlocation "$key")
  loadpath+=("$dependency_package_root/.gerbil/lib")
done
loadpath+=("$dependency_library_root")
test_files=()
for key in {test_keys}; do
  test_files+=("$(rlocation "$key")")
done
export GERBIL_PATH="$package_root/.gerbil"
export GERBIL_LOADPATH="$(IFS=:; printf '%s' "${{loadpath[*]}}")"
{environment_exports}
cd "$package_root"
exec "$gxtest" "$@" "${{test_files[@]}}"
""".format(
            dependency_keys = quoted_runfile_keys(ctx, dependency_roots),
            dependency_root_key = shell_quote(
                runfile_key(ctx, toolchain.dependency_library_root),
            ),
            environment_exports = environment_exports(
                ctx.attr.environment,
                "Gerbil test",
            ),
            gxtest_key = shell_quote(runfile_key(ctx, toolchain.gxtest.executable)),
            package_key = shell_quote(runfile_key(ctx, package.package_root)),
            runfiles_resolver = runfiles_resolver(),
            test_keys = quoted_runfile_keys(ctx, ctx.files.tests),
        ),
    )

    runfiles = ctx.runfiles(
        files = [
            package.package_root,
            toolchain.dependency_library_root,
            toolchain.gxtest.executable,
        ] + ctx.files.tests,
        transitive_files = depset(
            transitive = [
                package.dependency_roots,
                toolchain.runfiles,
            ],
        ),
    )
    for target in ctx.attr.data:
        runfiles = runfiles.merge(target[DefaultInfo].default_runfiles)
        runfiles = runfiles.merge(target[DefaultInfo].data_runfiles)

    return [DefaultInfo(
        executable = executable,
        runfiles = runfiles,
    )]

gerbil_test = rule(
    implementation = _gerbil_test_impl,
    attrs = {
        "data": attr.label_list(allow_files = True),
        "environment": attr.string_dict(),
        "package": attr.label(mandatory = True, providers = [GerbilPackageInfo]),
        "tests": attr.label_list(allow_files = True),
    },
    doc = "Runs gxtest against one built GerbilPackageInfo capability.",
    test = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)
