#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

normalize_system() {
  case "$1" in
    Darwin) printf 'darwin\n' ;;
    Linux) printf 'linux\n' ;;
    *) return 64 ;;
  esac
}

normalize_arch() {
  case "$1" in
    amd64 | x86_64) printf 'x86_64\n' ;;
    aarch64 | arm64) printf 'aarch64\n' ;;
    *) return 64 ;;
  esac
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

system="$(normalize_system "$(uname -s)")"
architecture="$(normalize_arch "$(uname -m)")"
mkdir -p "$test_root/consumer"
fixture=provided
archive="${GERBIL_PREBUILT_ARCHIVE:-}"
if [[ -z "$archive" ]]; then
  fixture=synthetic
  payload="$test_root/payload"
  mkdir -p "$payload/prefix/bin" "$payload/prefix/lib"
  printf 'fake dependency\n' >"$payload/prefix/lib/fake.ss"

  for tool in gxc gxi gxpkg gxtest; do
    if [[ "$tool" == gxi ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'if [[ "${1:-}" == --version ]]; then printf "Gerbil v0.prebuilt-test\\n"; fi' \
        'exit 0' >"$payload/prefix/bin/$tool"
    else
      printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$payload/prefix/bin/$tool"
    fi
    chmod +x "$payload/prefix/bin/$tool"
  done

  jq -n \
    --arg system "$system" \
    --arg architecture "$architecture" \
    '{
      schema: "gerbil-bazel.prebuilt-capability-manifest.v1",
      capabilityId: "synthetic-prebuilt-test",
      version: "Gerbil v0.prebuilt-test",
      nativeAbiFingerprint: "0000000000000000000000000000000000000000",
      platform: {os: $system, arch: $architecture},
      gerbilHome: "prefix",
      tools: {
        gxc: "prefix/bin/gxc",
        gxi: "prefix/bin/gxi",
        gxpkg: "prefix/bin/gxpkg",
        gxtest: "prefix/bin/gxtest"
      },
      dependencyRoots: ["prefix/lib"],
      environment: {}
    }' >"$payload/gerbil-bazel-capability.json"

  archive="$test_root/prebuilt.tar.gz"
  tar -C "$payload" -czf "$archive" .
  manifest="$payload/gerbil-bazel-capability.json"
else
  archive="$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")"
  if [[ ! -f "$archive" ]]; then
    printf 'provided Gerbil capability archive does not exist: %s\n' "$archive" >&2
    exit 66
  fi
  manifest="${archive%.tar.gz}.manifest.json"
  if [[ ! -f "$manifest" ]]; then
    manifest="$test_root/provided-manifest.json"
    tar -xOzf "$archive" ./gerbil-bazel-capability.json >"$manifest"
  fi
fi

expected_version="$(jq -er '.version' "$manifest")"
archive_sha256="$(sha256_file "$archive")"
archive_url="file://$archive"

sed \
  -e "s|@@GERBIL_BAZEL_PATH@@|$repo_root|g" \
  -e "s|@@ARCHIVE_URL@@|$archive_url|g" \
  -e "s|@@ARCHIVE_SHA256@@|$archive_sha256|g" \
  "$repo_root/tests/prebuilt/MODULE.bazel.tpl" \
  >"$test_root/consumer/MODULE.bazel"
cp "$repo_root/tests/prebuilt/BUILD.bazel" "$test_root/consumer/BUILD.bazel"

(
  cd "$test_root/consumer"
  provider_started_at="$SECONDS"
  bazel --output_user_root="$test_root/bazel" query \
    @prebuilt_gerbil//:registered_toolchain
  provider_seconds="$((SECONDS - provider_started_at))"
  tool_started_at="$SECONDS"
  observed_version="$(
    bazel --output_user_root="$test_root/bazel" run \
      @prebuilt_gerbil//:gxi -- --version 2>/dev/null
  )"
  if [[ "$observed_version" != "$expected_version" ]]; then
    printf 'prebuilt repository runtime probe mismatch: expected %s, got %s\n' \
      "$expected_version" "$observed_version" >&2
    exit 1
  fi
  tool_seconds="$((SECONDS - tool_started_at))"
  jq -cn \
    --arg schema gerbil-bazel.prebuilt-repository-test-receipt.v1 \
    --arg fixture "$fixture" \
    --arg version "$observed_version" \
    --argjson provider_seconds "$provider_seconds" \
    --argjson tool_seconds "$tool_seconds" \
    '{
      schema: $schema,
      outcome: "passed",
      fixture: $fixture,
      version: $version,
      providerSeconds: $provider_seconds,
      toolSeconds: $tool_seconds,
      totalSeconds: ($provider_seconds + $tool_seconds)
    }'
)
