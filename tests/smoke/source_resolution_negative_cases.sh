#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <bazel-binary> <gerbil-bazel-root>" >&2
  exit 2
fi

bazel_binary="$1"
gerbil_bazel_root="$2"

if [[ ! -x "$bazel_binary" ]]; then
  echo "bazel binary is not executable: $bazel_binary" >&2
  exit 2
fi
if [[ ! -f "$gerbil_bazel_root/MODULE.bazel" ]]; then
  echo "gerbil-bazel root is invalid: $gerbil_bazel_root" >&2
  exit 2
fi

fixture_root="$(mktemp -d "${TMPDIR:-/tmp}/gerbil-bazel-source-negative.XXXXXX")"
if [[ "${KEEP_FIXTURES:-0}" == "1" ]]; then
  printf 'keeping negative fixtures at %s\n' "$fixture_root" >&2
else
  trap 'rm -rf "$fixture_root"' EXIT
fi

write_workspace() {
  local workspace="$1"
  mkdir -p "$workspace"
  cat >"$workspace/BUILD.bazel" <<'EOF'
exports_files(
    ["project-root.marker"],
    visibility = ["//visibility:public"],
)
EOF
  printf '%s\n' 'gerbil-bazel source-resolution negative fixture' >"$workspace/project-root.marker"
}

write_module() {
  local workspace="$1"
  local package="$2"
  local source_repo="$3"
  local identified_block="$4"
  cat >"$workspace/MODULE.bazel" <<EOF
module(
    name = "source_resolution_${package//-/_}",
    version = "0.0.0",
)

bazel_dep(name = "gerbil_bazel", version = "0.1.0")
local_path_override(
    module_name = "gerbil_bazel",
    path = "$gerbil_bazel_root",
)

gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.host(
    name = "fixture_host",
    project_root_marker = "//:project-root.marker",
    project_library_relative_path = "project-library",
    project_dependency_source_packages = ["$package"],
$identified_block
)
use_repo(gerbil, "$source_repo")
EOF
}

run_negative_case() {
  local case_name="$1"
  local package="$2"
  local source_repo="$3"
  local expected_outcome="$4"
  local expected_diagnostic="$5"
  local identified_block="${6:-}"
  local workspace="$fixture_root/$case_name"
  local log="$fixture_root/$case_name.log"

  write_workspace "$workspace"
  write_module "$workspace" "$package" "$source_repo" "$identified_block"

  case "$case_name" in
    compiled-only)
      mkdir -p "$workspace/.gerbil/pkg/compiled-only"
      printf '%s\n' 'exports_files([])' >"$workspace/.gerbil/pkg/compiled-only/BUILD.bazel"
      ;;
    ambiguous)
      mkdir -p "$workspace/.gerbil/pkg/ambiguous" "$workspace/project-library/ambiguous"
      printf '%s\n' '(export ambiguous-checkout)' >"$workspace/.gerbil/pkg/ambiguous/source.ss"
      printf '%s\n' '(export ambiguous-library)' >"$workspace/project-library/ambiguous/source.ss"
      ;;
    invalid-revision)
      mkdir -p "$workspace/.gerbil/pkg/clan"
      printf '%s\n' 'ready' >"$workspace/.gerbil/pkg/clan/ready.txt"
      git -C "$workspace" init -q
      git -C "$workspace" -c user.name='gerbil-bazel fixture' \
        -c user.email='fixture@example.invalid' add .
      GIT_AUTHOR_DATE='2000-01-01T00:00:00+0000' \
        GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000' \
        git -C "$workspace" -c user.name='gerbil-bazel fixture' \
          -c user.email='fixture@example.invalid' commit -q \
          -m 'invalid revision fixture'
      git -C "$workspace" remote add origin \
        https://example.invalid/gerbil-bazel-negative-fixture.git
      ;;
  esac

  if ! (
      cd "$workspace"
      "$bazel_binary" \
        --output_user_root="$fixture_root/output-$case_name" \
        mod deps \
        --lockfile_mode=off
    ) >"$log" 2>&1; then
    echo "failed to initialize negative source-resolution module: $case_name" >&2
    sed -n '1,160p' "$log" >&2
    exit 1
  fi

  if (
      cd "$workspace"
      "$bazel_binary" \
        --output_user_root="$fixture_root/output-$case_name" \
        query "@$source_repo//:sources" \
        --lockfile_mode=off
    ) >>"$log" 2>&1; then
    echo "negative source-resolution case unexpectedly succeeded: $case_name" >&2
    exit 1
  fi
  if ! grep -Fq "$expected_diagnostic" "$log"; then
    echo "negative source-resolution case emitted the wrong diagnostic: $case_name" >&2
    sed -n '1,160p' "$log" >&2
    exit 1
  fi
  if ! grep -Eq "\"outcome\"[[:space:]]*:[[:space:]]*\"$expected_outcome\"" "$log"; then
    echo "negative source-resolution case omitted its structured outcome: $case_name" >&2
    sed -n '1,160p' "$log" >&2
    exit 1
  fi
  printf 'PASS %s outcome=%s: %s\n' \
    "$case_name" "$expected_outcome" "$expected_diagnostic"
}

run_negative_case \
  missing \
  missing \
  missing_sources \
  missing \
  'project dependency package does not exist: missing'

run_negative_case \
  compiled-only \
  compiled-only \
  compiled_only_sources \
  compiled-artifact-only \
  'project dependency package has no source files: compiled-only'

run_negative_case \
  ambiguous \
  ambiguous \
  ambiguous_sources \
  ambiguous \
  'project dependency source resolution is ambiguous: ambiguous'

run_negative_case \
  invalid-revision \
  clan \
  clan_sources \
  revision-mismatch \
  'project dependency revision mismatch: expected HEAD, resolved' \
  '    project_dependency_source_paths = {"clan": ".gerbil/pkg/clan"},
    project_dependency_source_revisions = {"clan": "HEAD"},
    project_dependency_source_uris = {
        "clan": "https://example.invalid/gerbil-bazel-negative-fixture",
    },'
