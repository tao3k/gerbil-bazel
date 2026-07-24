"""Lifecycle-safe public test rule for built Gerbil packages."""

load(":providers.bzl", "GerbilPackageInfo")
load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

_ENV_FIRST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
_ENV_REST = _ENV_FIRST + "0123456789"

def _runfile_key(ctx, file):
    if file.short_path.startswith("../"):
        return file.short_path[3:]
    return "{}/{}".format(ctx.workspace_name, file.short_path)

def _shell_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"

def _environment_exports(environment):
    exports = []
    for name in sorted(environment.keys()):
        if not name or name[0] not in _ENV_FIRST:
            fail("invalid Gerbil test environment name: {}".format(name))
        for index in range(1, len(name)):
            if name[index] not in _ENV_REST:
                fail("invalid Gerbil test environment name: {}".format(name))
        exports.append("export {}={}".format(name, _shell_quote(environment[name])))
    return "\n".join(exports)

def _quoted_runfile_keys(ctx, files):
    return " ".join([
        _shell_quote(_runfile_key(ctx, file))
        for file in files
    ])

def _runfiles_resolver():
    return """rlocation() {
  local key=$1
  local runfiles_dir=${RUNFILES_DIR:-${BASH_SOURCE[0]}.runfiles}
  local runfiles_manifest=${RUNFILES_MANIFEST_FILE:-${BASH_SOURCE[0]}.runfiles_manifest}
  if [[ -e "$runfiles_dir/$key" ]]; then
    printf '%s\\n' "$runfiles_dir/$key"
    return 0
  fi
  if [[ -f "$runfiles_manifest" ]]; then
    local manifest_key
    local manifest_path
    while IFS=' ' read -r manifest_key manifest_path; do
      if [[ "$manifest_key" == "$key" ]]; then
        printf '%s\\n' "$manifest_path"
        return 0
      fi
    done < "$runfiles_manifest"
  fi
  printf 'cannot resolve runfile: %s\\n' "$key" >&2
  return 1
}
"""

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
            dependency_keys = _quoted_runfile_keys(ctx, dependency_roots),
            dependency_root_key = _shell_quote(
                _runfile_key(ctx, toolchain.dependency_library_root),
            ),
            environment_exports = _environment_exports(ctx.attr.environment),
            gxtest_key = _shell_quote(_runfile_key(ctx, toolchain.gxtest.executable)),
            package_key = _shell_quote(_runfile_key(ctx, package.package_root)),
            runfiles_resolver = _runfiles_resolver(),
            test_keys = _quoted_runfile_keys(ctx, ctx.files.tests),
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
