#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
mkdir -p "$test_root/bin"

cat >"$test_root/bin/cc" <<'EOF'
#!/usr/bin/env bash
printf 'synthetic-cc %s\n' "${SYNTHETIC_CC_VERSION:-1}"
EOF
cat >"$test_root/bin/ld" <<'EOF'
#!/usr/bin/env bash
printf 'synthetic-ld 1\n'
EOF
cat >"$test_root/bin/pkg-config" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == --modversion ]]; then
  printf '%s-version-1\n' "${2:?module is required}"
  exit 0
fi
exit 64
EOF
cat >"$test_root/bin/ccache" <<'EOF'
#!/usr/bin/env bash
printf 'synthetic-ccache %s\n' "${SYNTHETIC_CCACHE_VERSION:-1}"
EOF
chmod +x \
  "$test_root/bin/cc" \
  "$test_root/bin/ccache" \
  "$test_root/bin/ld" \
  "$test_root/bin/pkg-config"

base_config="$repo_root/tools/ci/gerbil_source_build_config.json"
execution_policy_config="$test_root/execution-policy.json"
output_config="$test_root/output-config.json"
jq '.executionPolicy.compilerCache.maxSize = "4G"' \
  "$base_config" >"$execution_policy_config"
jq '.outputIdentity.configureArguments += ["--disable-shared"]' \
  "$base_config" >"$output_config"

run_identity() {
  local name=$1
  local ref=$2
  local config=$3
  local compiler_version=$4
  local ccache_version=$5
  local receipt="$test_root/$name.json"
  SYNTHETIC_CC_VERSION="$compiler_version" \
    SYNTHETIC_CCACHE_VERSION="$ccache_version" \
    GERBIL_REF="$ref" \
    GERBIL_SOURCE_BUILD_CONFIG="$config" \
    GERBIL_SOURCE_BUILD_COMPILER_EXECUTABLE="$test_root/bin/cc" \
    GERBIL_SOURCE_BUILD_CCACHE_EXECUTABLE="$test_root/bin/ccache" \
    GERBIL_SOURCE_BUILD_LINKER_EXECUTABLE="$test_root/bin/ld" \
    GERBIL_SOURCE_BUILD_PKG_CONFIG_EXECUTABLE="$test_root/bin/pkg-config" \
    GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$receipt" \
    "$repo_root/tools/ci/source_build_identity.sh" >/dev/null
  jq -e '.schema == "gerbil-bazel.source-build-identity.v1"' "$receipt" >/dev/null
}

run_identity baseline-a ref-a "$base_config" 1 1
run_identity baseline-b ref-a "$base_config" 1 1
run_identity revision-delta ref-b "$base_config" 1 1
run_identity execution-policy-delta ref-a "$execution_policy_config" 1 1
run_identity output-delta ref-a "$output_config" 1 1
run_identity compiler-delta ref-a "$base_config" 2 1
run_identity ccache-delta ref-a "$base_config" 1 2

field() {
  jq -er "$2" "$test_root/$1.json"
}

baseline_install="$(field baseline-a .installDigest)"
baseline_ccache="$(field baseline-a .compilerCacheNamespaceDigest)"

[[ "$baseline_install" == "$(field baseline-b .installDigest)" ]]
[[ "$baseline_ccache" == "$(field baseline-b .compilerCacheNamespaceDigest)" ]]

[[ "$baseline_install" != "$(field revision-delta .installDigest)" ]]
[[ "$baseline_ccache" == "$(field revision-delta .compilerCacheNamespaceDigest)" ]]

[[ "$baseline_install" == "$(field execution-policy-delta .installDigest)" ]]
[[ "$baseline_ccache" == "$(field execution-policy-delta .compilerCacheNamespaceDigest)" ]]
[[ "$(field baseline-a .config.digest)" != "$(field execution-policy-delta .config.digest)" ]]

[[ "$baseline_install" != "$(field output-delta .installDigest)" ]]
[[ "$baseline_ccache" != "$(field output-delta .compilerCacheNamespaceDigest)" ]]

[[ "$baseline_install" != "$(field compiler-delta .installDigest)" ]]
[[ "$baseline_ccache" != "$(field compiler-delta .compilerCacheNamespaceDigest)" ]]

[[ "$baseline_install" == "$(field ccache-delta .installDigest)" ]]
[[ "$baseline_ccache" != "$(field ccache-delta .compilerCacheNamespaceDigest)" ]]
