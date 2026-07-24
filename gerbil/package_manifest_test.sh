#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local logical_path="$1"
  local candidate

  if [[ "$logical_path" = /* && -e "$logical_path" ]]; then
    printf '%s\n' "$logical_path"
    return 0
  fi

  for runfiles_root in "${RUNFILES_DIR:-}" "${TEST_SRCDIR:-}"; do
    if [[ -n "$runfiles_root" ]]; then
      candidate="$runfiles_root/$logical_path"
      if [[ -e "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
      fi
    fi
  done

  if [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
    candidate="$(
      awk -v logical_path="$logical_path" '
        index($0, logical_path " ") == 1 {
          print substr($0, length(logical_path) + 2)
          exit
        }
      ' "$RUNFILES_MANIFEST_FILE"
    )"
    if [[ -n "$candidate" && -e "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  printf 'runfile not found: %s\n' "$logical_path" >&2
  return 1
}

gxi="$(resolve_runfile "$1")"
evaluator="$(resolve_runfile "$2")"
fixture_manifest="$(resolve_runfile "$3")"

test_root="$(mktemp -d "${TMPDIR:-/tmp}/gerbil-package-manifest.XXXXXX")"
cleanup() {
  rm -rf -- "$test_root"
}
trap cleanup EXIT

fixture_root="$(dirname "$fixture_manifest")"
cp -RL "$fixture_root" "$test_root/package"

first="$test_root/first.json"
second="$test_root/second.json"
changed="$test_root/changed.json"
ignored_bazel_metadata="$test_root/ignored-bazel-metadata.json"

"$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >"$first"
"$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >"$second"
cmp "$first" "$second"

jq -e '
  .schema == "gerbil-bazel.package-manifest.v1" and
  .package == "example.invalid/root" and
  .manifest == "gerbil.pkg" and
  (has("build") | not) and
  .dependencies == [
    {
      "package": "example.invalid/dep",
      "raw": "example.invalid/dep@v1.2.3",
      "tag": "v1.2.3"
    },
    {
      "package": "example.invalid/plain",
      "raw": "example.invalid/plain",
      "tag": null
    }
  ] and
  .extensions == [{"datum": "(sandboxed)", "key": "policy"}] and
  ([.sources[].path] == ([.sources[].path] | sort)) and
  (.sources | any(.path == "build.ss")) and
  (.sources | any(.path == "gerbil.pkg")) and
  (.sources | all(.sha256 | test("^[0-9a-f]{64}$"))) and
  (.closureSha256 | test("^[0-9a-f]{64}$"))
' "$first" >/dev/null

printf '\n;; source identity change\n' >>"$test_root/package/src/main.ss"
"$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >"$changed"
test "$(jq -r .closureSha256 "$first")" != "$(jq -r .closureSha256 "$changed")"

rm -f -- "$test_root/package/build.ss"
if "$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >/dev/null 2>&1; then
  echo "missing build.ss unexpectedly passed" >&2
  exit 1
fi

cp -L "$fixture_root/build.ss" "$test_root/package/build.ss"
touch "$test_root/package/BUILD.bazel"
"$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >"$ignored_bazel_metadata"
cmp "$changed" "$ignored_bazel_metadata"
jq -e '(.sources | all(.path != "BUILD.bazel"))' "$ignored_bazel_metadata" >/dev/null

rm -f -- "$test_root/package/BUILD.bazel"
ln -s src/main.ss "$test_root/package/symlink.ss"
if "$gxi" "$evaluator" "$test_root/package/gerbil.pkg" >/dev/null 2>&1; then
  echo "symbolic link unexpectedly passed" >&2
  exit 1
fi

echo "Gerbil package manifest evaluator: ok"
