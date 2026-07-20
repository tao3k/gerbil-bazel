#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_REF:?GERBIL_REF is required}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
config_path="${GERBIL_SOURCE_BUILD_CONFIG:-$repo_root/tools/ci/gerbil_source_build_config.json}"
receipt_path="${GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT:-$repo_root/.ci/gerbil-source-build-identity.json}"
source_url="${GERBIL_SOURCE_URL:-https://github.com/mighty-gerbils/gerbil.git}"
compiler_command="${GERBIL_SOURCE_BUILD_COMPILER_COMMAND:-${CC:-cc}}"
compiler_executable="${GERBIL_SOURCE_BUILD_COMPILER_EXECUTABLE:-${compiler_command%% *}}"
linker_executable="${GERBIL_SOURCE_BUILD_LINKER_EXECUTABLE:-ld}"
pkg_config_executable="${GERBIL_SOURCE_BUILD_PKG_CONFIG_EXECUTABLE:-pkg-config}"
ccache_executable="${GERBIL_SOURCE_BUILD_CCACHE_EXECUTABLE:-ccache}"

sha256_stream() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  else
    shasum -a 256 | awk '{print $1}'
  fi
}

resolve_executable() {
  local executable=$1
  local resolved
  resolved="$(command -v "$executable" || true)"
  if [[ -z "$resolved" ]]; then
    printf 'source build identity executable is unavailable: %s\n' "$executable" >&2
    return 69
  fi
  printf '%s\n' "$resolved"
}

command_version() {
  local executable=$1
  local version
  version="$("$executable" --version 2>&1 || true)"
  if [[ -z "$version" ]]; then
    version="$("$executable" -v 2>&1 || true)"
  fi
  if [[ -z "$version" ]]; then
    printf 'version-unavailable\n'
  else
    printf '%s\n' "$version"
  fi
}

package_version() {
  local module=$1
  local version
  version="$("$pkg_config_path" --modversion "$module" 2>/dev/null || true)"
  printf '%s\n' "${version:-unavailable}"
}

compiler_path="$(resolve_executable "$compiler_executable")"
linker_path="$(resolve_executable "$linker_executable")"
pkg_config_path="$(resolve_executable "$pkg_config_executable")"
ccache_path="$(command -v "$ccache_executable" || true)"
if [[ -n "$ccache_path" ]]; then
  ccache_version="$(command_version "$ccache_path")"
else
  ccache_path=unavailable
  ccache_version=unavailable
fi

config_json="$(
  jq -cSe '
    select(.schema == "gerbil-bazel.source-build-config.v1") |
    select(.contractVersion == 1) |
    select(.outputIdentity.configureArguments | type == "array") |
    select(.outputIdentity.upstreamEntrypoints == {
      configure: "./configure",
      build: "make",
      install: "make install"
    }) |
    select(
      .executionPolicy.buildTimeoutMinutes as $timeout |
      ($timeout | type) == "number" and
      $timeout > 0 and
      $timeout <= 360 and
      ($timeout | floor) == $timeout
    ) |
    select(
      .executionPolicy.terminationGraceSeconds as $grace |
      ($grace | type) == "number" and
      $grace > 0 and
      $grace <= 300 and
      ($grace | floor) == $grace
    ) |
    select(.executionPolicy.parallelism == {
      source: "available-logical-cpus",
      makeArgument: "-j"
    }) |
    select(.executionPolicy.compilerCache.tool == "ccache")
  ' "$config_path"
)"
if [[ -z "$config_json" ]]; then
  printf 'invalid Gerbil source build configuration: %s\n' "$config_path" >&2
  exit 65
fi

build_timeout_minutes="$(jq -er '.executionPolicy.buildTimeoutMinutes' <<<"$config_json")"
termination_grace_seconds="$(jq -er '.executionPolicy.terminationGraceSeconds' <<<"$config_json")"
output_config_json="$(jq -cS '.outputIdentity' <<<"$config_json")"
config_digest="$(printf '%s' "$config_json" | sha256_stream)"
output_config_digest="$(printf '%s' "$output_config_json" | sha256_stream)"
compiler_version="$(command_version "$compiler_path")"
linker_version="$(command_version "$linker_path")"
dependency_versions="$(
  jq -cnS \
    --arg openssl "$(package_version openssl)" \
    --arg sqlite3 "$(package_version sqlite3)" \
    --arg zlib "$(package_version zlib)" \
    '{openssl: $openssl, sqlite3: $sqlite3, zlib: $zlib}'
)"
build_environment="$(
  jq -cnS \
    --arg cflags "${CFLAGS:-}" \
    --arg cppflags "${CPPFLAGS:-}" \
    --arg ldflags "${LDFLAGS:-}" \
    --arg library_path "${LIBRARY_PATH:-}" \
    --arg pkg_config_path "${PKG_CONFIG_PATH:-}" \
    --arg sdkroot "${SDKROOT:-}" \
    '{
      CFLAGS: $cflags,
      CPPFLAGS: $cppflags,
      LDFLAGS: $ldflags,
      LIBRARY_PATH: $library_path,
      PKG_CONFIG_PATH: $pkg_config_path,
      SDKROOT: $sdkroot
    }'
)"
native_build_identity="$(
  jq -cnS \
    --arg system "$(uname -s)" \
    --arg architecture "$(uname -m)" \
    --arg compiler_command "$compiler_command" \
    --arg compiler_path "$compiler_path" \
    --arg compiler_version "$compiler_version" \
    --arg linker_path "$linker_path" \
    --arg linker_version "$linker_version" \
    --arg output_config_digest "$output_config_digest" \
    --argjson dependency_versions "$dependency_versions" \
    --argjson environment "$build_environment" \
    '{
      system: $system,
      architecture: $architecture,
      compiler: {
        command: $compiler_command,
        path: $compiler_path,
        version: $compiler_version
      },
      linker: {path: $linker_path, version: $linker_version},
      outputConfigDigest: $output_config_digest,
      dependencyVersions: $dependency_versions,
      environment: $environment
    }'
)"
compiler_cache_identity="$(
  jq -cnS \
    --arg ccache_path "$ccache_path" \
    --arg ccache_version "$ccache_version" \
    --argjson native_build_identity "$native_build_identity" \
    '{
      nativeBuildIdentity: $native_build_identity,
      tool: {path: $ccache_path, version: $ccache_version}
    }'
)"
compiler_cache_namespace_digest="$(
  printf '%s' "$compiler_cache_identity" | sha256_stream
)"
install_material="$(
  jq -cnS \
    --arg source_ref "$GERBIL_REF" \
    --arg source_url "$source_url" \
    --argjson native_build_identity "$native_build_identity" \
    '{
      sourceRef: $source_ref,
      sourceUrl: $source_url,
      nativeBuildIdentity: $native_build_identity
    }'
)"
install_digest="$(printf '%s' "$install_material" | sha256_stream)"

mkdir -p "$(dirname "$receipt_path")"
jq -nS \
  --arg schema gerbil-bazel.source-build-identity.v1 \
  --arg source_ref "$GERBIL_REF" \
  --arg source_url "$source_url" \
  --arg config_digest "$config_digest" \
  --arg output_config_digest "$output_config_digest" \
  --arg compiler_cache_namespace_digest "$compiler_cache_namespace_digest" \
  --arg install_digest "$install_digest" \
  --argjson config "$config_json" \
  --argjson native_build_identity "$native_build_identity" \
  --argjson compiler_cache_identity "$compiler_cache_identity" \
  '{
    schema: $schema,
    digestAlgorithm: "sha256",
    source: {ref: $source_ref, url: $source_url},
    config: {
      digest: $config_digest,
      outputIdentityDigest: $output_config_digest,
      value: $config
    },
    nativeBuildIdentity: $native_build_identity,
    compilerCacheIdentity: $compiler_cache_identity,
    compilerCacheNamespaceDigest: $compiler_cache_namespace_digest,
    installDigest: $install_digest
  }' >"$receipt_path"

printf 'install_digest=%s\n' "$install_digest"
printf 'compiler_cache_namespace_digest=%s\n' "$compiler_cache_namespace_digest"
printf 'config_digest=%s\n' "$config_digest"
printf 'build_timeout_minutes=%s\n' "$build_timeout_minutes"
printf 'termination_grace_seconds=%s\n' "$termination_grace_seconds"
printf 'receipt=%s\n' "$receipt_path"
