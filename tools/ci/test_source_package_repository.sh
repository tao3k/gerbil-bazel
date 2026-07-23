#!/usr/bin/env bash
set -euo pipefail

bazel_bin="${BAZEL:-bazelisk}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(cd "$(mktemp -d)" && pwd -P)"
cleanup() {
  if [[ "${GERBIL_SOURCE_PACKAGE_TEST_KEEP_ROOT:-0}" == 1 ]]; then
    printf 'preserved source-package test root: %s\n' "$test_root" >&2
  else
    rm -rf "$test_root"
  fi
}
trap cleanup EXIT

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

make_archive() {
  local name="$1"
  local fixture="$test_root/$name"
  mkdir -p "$fixture/src"
  printf '(package: fixture)\n' >"$fixture/gerbil.pkg"
  printf '(displayln \"fixture\")\n' >"$fixture/build.ss"
  printf '(export fixture)\n' >"$fixture/src/fixture.ss"
  case "$name" in
    reserved) printf '{}\n' >"$fixture/source-package.json" ;;
    symlink) ln -s gerbil.pkg "$fixture/package-link" ;;
  esac
  tar -czf "$test_root/$name.tar.gz" -C "$fixture" .
}

write_module() {
  local archive="$1"
  local digest="$2"
  cat >"$test_root/consumer/MODULE.bazel" <<EOF
module(name = "source_package_consumer")

bazel_dep(name = "gerbil_bazel", version = "0.1.0")
local_path_override(module_name = "gerbil_bazel", path = "$repo_root")

gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.source_package(
    name = "fixture_sources",
    package = "fixture",
    sha256 = "$digest",
    urls = ["file://$archive"],
)
use_repo(gerbil, "fixture_sources")
EOF
}

expect_failure() {
  local scenario="$1"
  local archive="$2"
  local digest="$3"
  local expected="$4"
  local log="$test_root/$scenario.log"
  write_module "$archive" "$digest"
  set +e
  (
    cd "$test_root/consumer"
    "$bazel_bin" --output_user_root="$test_root/bazel-$scenario" query \
      --lockfile_mode=off @fixture_sources//:sources
  ) >"$log" 2>&1
  local status=$?
  set -e
  if [[ "$status" == 0 ]]; then
    printf 'source package scenario %s unexpectedly succeeded\n' "$scenario" >&2
    exit 1
  fi
  grep -F "$expected" "$log" >/dev/null
}

mkdir -p "$test_root/consumer"
make_archive valid
make_archive reserved
make_archive symlink

valid_archive="$test_root/valid.tar.gz"
valid_sha256="$(sha256_file "$valid_archive")"
expect_failure empty-digest "$valid_archive" "" \
  'sha256 must contain 64 hexadecimal characters'
expect_failure short-digest "$valid_archive" "$(printf 'a%.0s' {1..63})" \
  'sha256 must contain 64 hexadecimal characters'
expect_failure non-hex-digest "$valid_archive" "$(printf 'g%.0s' {1..64})" \
  'sha256 must contain 64 hexadecimal characters'
expect_failure reserved-path "$test_root/reserved.tar.gz" \
  "$(sha256_file "$test_root/reserved.tar.gz")" \
  'downloaded Gerbil package uses reserved path: source-package.json'
expect_failure symlink "$test_root/symlink.tar.gz" \
  "$(sha256_file "$test_root/symlink.tar.gz")" \
  'downloaded Gerbil package symlinks are unsupported: package-link'

printf '{"schema":"gerbil.source-package-validation.v1","valid_sha256":"%s","scenarios":5}\n' \
  "$valid_sha256"
