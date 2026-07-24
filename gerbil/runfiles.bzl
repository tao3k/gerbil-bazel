"""Shared runfiles and environment helpers for Gerbil launchers."""

_ENV_FIRST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
_ENV_REST = _ENV_FIRST + "0123456789"

def runfile_key(ctx, file):
    if file.short_path.startswith("../"):
        return file.short_path[3:]
    return "{}/{}".format(ctx.workspace_name, file.short_path)

def shell_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"

def environment_exports(environment, owner):
    exports = []
    for name in sorted(environment.keys()):
        if not name or name[0] not in _ENV_FIRST:
            fail("invalid {} environment name: {}".format(owner, name))
        for index in range(1, len(name)):
            if name[index] not in _ENV_REST:
                fail("invalid {} environment name: {}".format(owner, name))
        exports.append("export {}={}".format(name, shell_quote(environment[name])))
    return "\n".join(exports)

def quoted_runfile_keys(ctx, files):
    return " ".join([
        shell_quote(runfile_key(ctx, file))
        for file in files
    ])

def runfiles_resolver():
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
