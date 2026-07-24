"""Public package-aware executable launcher for Gerbil consumers."""

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

def _gerbil_package_binary_impl(ctx):
    package = ctx.attr.package[GerbilPackageInfo]
    toolchain = resolved_gerbil_toolchain(ctx)
    dependency_roots = package.dependency_roots.to_list()
    launcher = ctx.actions.declare_file(ctx.label.name)

    ctx.actions.write(
        output = launcher,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
{runfiles_resolver}
gxi=$(rlocation {gxi_key})
script=$(rlocation {script_key})
package_root=$(rlocation {package_key})
dependency_root_marker=$(rlocation {dependency_root_key})
dependency_library_root=$(dirname "$dependency_root_marker")
loadpath=("$package_root/.gerbil/lib")
for key in {dependency_keys}; do
  dependency_package_root=$(rlocation "$key")
  loadpath+=("$dependency_package_root/.gerbil/lib")
done
loadpath+=("$dependency_library_root")
export GERBIL_PATH="$package_root/.gerbil"
export GERBIL_LOADPATH="$(IFS=:; printf '%s' "${{loadpath[*]}}")"
{environment_exports}
cd "$package_root"
exec "$gxi" "$script" {declared_args} "$@"
""".format(
            declared_args = " ".join([shell_quote(value) for value in ctx.attr.args]),
            dependency_keys = quoted_runfile_keys(ctx, dependency_roots),
            dependency_root_key = shell_quote(
                runfile_key(ctx, toolchain.dependency_library_root),
            ),
            environment_exports = environment_exports(
                ctx.attr.environment,
                "Gerbil package binary",
            ),
            gxi_key = shell_quote(runfile_key(ctx, toolchain.gxi.executable)),
            package_key = shell_quote(runfile_key(ctx, package.package_root)),
            runfiles_resolver = runfiles_resolver(),
            script_key = shell_quote(runfile_key(ctx, ctx.file.script)),
        ),
    )

    runfiles = ctx.runfiles(
        files = [
            ctx.file.script,
            package.package_root,
            toolchain.dependency_library_root,
            toolchain.gxi.executable,
        ],
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
        executable = launcher,
        runfiles = runfiles,
    )]

gerbil_package_binary = rule(
    implementation = _gerbil_package_binary_impl,
    attrs = {
        "data": attr.label_list(allow_files = True),
        "environment": attr.string_dict(),
        "package": attr.label(mandatory = True, providers = [GerbilPackageInfo]),
        "script": attr.label(allow_single_file = True, mandatory = True),
    },
    doc = (
        "Runs an explicit Scheme entry script against one built " +
        "GerbilPackageInfo capability."
    ),
    executable = True,
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)
