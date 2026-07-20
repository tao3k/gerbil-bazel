#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

fixture_bin="$test_root/fixture-bin"
mkdir -p "$fixture_bin"
cat >"$fixture_bin/uname" <<'EOF'
#!/usr/bin/env bash
case "${1:-}" in
  -s) printf '%s\n' "${SYNTHETIC_RUNNER_SYSTEM:?}" ;;
  -m) printf '%s\n' "${SYNTHETIC_RUNNER_ARCHITECTURE:?}" ;;
  *) exit 64 ;;
esac
EOF
cat >"$fixture_bin/getconf" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == _NPROCESSORS_ONLN ]] || exit 64
printf '%s\n' "${SYNTHETIC_AVAILABLE_LOGICAL_CPUS:?}"
EOF
cat >"$fixture_bin/sysctl" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == -n && "${2:-}" == hw.logicalcpu ]] || exit 64
printf '%s\n' "${SYNTHETIC_AVAILABLE_LOGICAL_CPUS:?}"
EOF
chmod +x "$fixture_bin/getconf" "$fixture_bin/sysctl" "$fixture_bin/uname"

prefix="$test_root/prefix"
install_digest="$(printf 'a%.0s' {1..64})"
mkdir -p "$prefix/bin"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$prefix/bin/gxi"
chmod +x "$prefix/bin/gxi"
jq -n \
  --arg install_digest "$install_digest" \
  '{
    schema: "gerbil-bazel.gerbil-bootstrap-receipt.v1",
    outcome: "ready",
    source_build_identity: {
      schema: "gerbil-bazel.source-build-identity.v1",
      installDigest: $install_digest
    }
  }' >"$prefix/bootstrap.receipt.json"

run_case() {
  local cache_hit=$1
  local expected=$2
  local system=$3
  local architecture=$4
  local cpu_count=$5
  local expected_system
  local expected_architecture
  local receipt="$test_root/$expected.json"
  case "$system" in
    Darwin) expected_system=darwin ;;
    Linux) expected_system=linux ;;
    *) exit 64 ;;
  esac
  case "$architecture" in
    amd64 | x86_64) expected_architecture=x86_64 ;;
    arm64 | aarch64) expected_architecture=aarch64 ;;
    *) exit 64 ;;
  esac
  PATH="$fixture_bin:$PATH" \
    SYNTHETIC_RUNNER_SYSTEM="$system" \
    SYNTHETIC_RUNNER_ARCHITECTURE="$architecture" \
    SYNTHETIC_AVAILABLE_LOGICAL_CPUS="$cpu_count" \
    GERBIL_INSTALL_CACHE_HIT="$cache_hit" \
    GERBIL_INSTALL_DIGEST="$install_digest" \
    GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$receipt" \
    GERBIL_PREFIX="$prefix" \
    GERBIL_RUNNER_NAME=synthetic-runner \
    "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null
  jq -e \
    --arg expected "$expected" \
    --arg install_digest "$install_digest" \
    --arg expected_system "$expected_system" \
    --arg expected_architecture "$expected_architecture" \
    --argjson expected_cpu_count "$cpu_count" \
    '.schema == "gerbil-bazel.install-materialization-receipt.v1" and
     .outcome == "ready" and
     .materialization == $expected and
     .installDigest == $install_digest and
     .runner.name == "synthetic-runner" and
     .runner.system == $expected_system and
     .runner.architecture == $expected_architecture and
     .runner.availableLogicalCpuCount == $expected_cpu_count and
     (.producerReceipt.digest | test("^[0-9a-f]{64}$"))' \
    "$receipt" >/dev/null
}

run_case true cache-hit Linux amd64 7
run_case false built Darwin arm64 9

if PATH="$fixture_bin:$PATH" \
  SYNTHETIC_RUNNER_SYSTEM=Linux \
  SYNTHETIC_RUNNER_ARCHITECTURE=x86_64 \
  SYNTHETIC_AVAILABLE_LOGICAL_CPUS=7 \
  GERBIL_INSTALL_CACHE_HIT=true \
  GERBIL_INSTALL_DIGEST="$(printf 'b%.0s' {1..64})" \
  GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$test_root/mismatch.json" \
  GERBIL_PREFIX="$prefix" \
  GERBIL_RUNNER_NAME=synthetic-runner \
  "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null 2>&1; then
  printf 'materialization receipt accepted a mismatched install digest\n' >&2
  exit 1
fi

if PATH="$fixture_bin:$PATH" \
  SYNTHETIC_RUNNER_SYSTEM=Linux \
  SYNTHETIC_RUNNER_ARCHITECTURE=x86_64 \
  SYNTHETIC_AVAILABLE_LOGICAL_CPUS=7 \
  GERBIL_INSTALL_CACHE_HIT=true \
  GERBIL_INSTALL_DIGEST="$install_digest" \
  GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$test_root/missing-runner.json" \
  GERBIL_PREFIX="$prefix" \
  "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null 2>&1; then
  printf 'materialization receipt accepted a missing runner identity\n' >&2
  exit 1
fi

assert_rejected_runner() {
  local name=$1
  local runner_name=$2
  local system=$3
  local architecture=$4
  local cpu_count=$5
  if PATH="$fixture_bin:$PATH" \
    SYNTHETIC_RUNNER_SYSTEM="$system" \
    SYNTHETIC_RUNNER_ARCHITECTURE="$architecture" \
    SYNTHETIC_AVAILABLE_LOGICAL_CPUS="$cpu_count" \
    GERBIL_INSTALL_CACHE_HIT=true \
    GERBIL_INSTALL_DIGEST="$install_digest" \
    GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$test_root/rejected-$name.json" \
    GERBIL_PREFIX="$prefix" \
    GERBIL_RUNNER_NAME="$runner_name" \
    "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null 2>&1; then
    printf 'materialization receipt accepted invalid runner fixture: %s\n' \
      "$name" >&2
    exit 1
  fi
}

assert_rejected_runner whitespace-name '   ' Linux x86_64 7
assert_rejected_runner unsupported-system synthetic-runner Plan9 x86_64 7
assert_rejected_runner unsupported-architecture synthetic-runner Linux mips64 7
assert_rejected_runner zero-cpu synthetic-runner Linux x86_64 0
assert_rejected_runner nonnumeric-cpu synthetic-runner Darwin arm64 many
