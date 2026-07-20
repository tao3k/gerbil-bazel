#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
upstream="$test_root/upstream"
prefix="$test_root/prefix"
source_checkout="$test_root/source"
checkpoint_root="$test_root/checkpoint"
identity_receipt="$test_root/source-build-identity.json"
mkdir -p "$upstream" "$test_root/bin"

cat >"$upstream/configure" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
prefix=
for argument in "$@"; do
  case "$argument" in
    --prefix=*) prefix=${argument#--prefix=} ;;
  esac
done
: "${prefix:?configure requires --prefix}"
printf '%s\n' "$prefix" >.synthetic-prefix
printf 'synthetic build environment\n' >build-env.sh
EOF
cat >"$upstream/build.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
stage=${1:?stage is required}
case "$stage" in
  prepare | gambit | boot-gxi | stage0 | stage1 | stdlib | libgerbil | lang | r7rs-large | srfi | tools) ;;
  *) exit 64 ;;
esac
if [[ -n "${GERBIL_SYNTHETIC_FAIL_STAGE:-}" ]]; then
  if [[ "$GERBIL_SYNTHETIC_FAIL_STAGE" == "$stage" ]]; then
    exit "${GERBIL_SYNTHETIC_BUILD_EXIT:-42}"
  fi
elif [[ "${GERBIL_SYNTHETIC_BUILD_EXIT:-0}" -ne 0 ]]; then
  exit "$GERBIL_SYNTHETIC_BUILD_EXIT"
fi
printf '%s\n' "$stage" >>.synthetic-stages
mkdir -p build/bin build/lib
if [[ "$stage" == stage1 ]]; then
  cat >build/bin/gxi <<'INNER'
#!/usr/bin/env bash
printf 'Gerbil synthetic-bootstrap-test\n'
INNER
  chmod +x build/bin/gxi
fi
if [[ "$stage" == stdlib ]]; then
  mkdir -p build/lib/std
  printf 'complete synthetic stdlib\n' >build/lib/std/synthetic.scm
fi
EOF
chmod +x "$upstream/configure" "$upstream/build.sh"
git -C "$upstream" init --quiet
git -C "$upstream" add build.sh configure
git -C "$upstream" \
  -c user.name=gerbil-bazel \
  -c user.email=gerbil-bazel@example.invalid \
  commit --quiet -m fixture
source_ref="$(git -C "$upstream" rev-parse HEAD)"

cat >"$test_root/bin/make" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  install)
    prefix="$(<.synthetic-prefix)"
    mkdir -p "$prefix/bin"
    cp build/bin/gxi "$prefix/bin/gxi"
    ;;
  *)
    printf 'unexpected synthetic make arguments: %s\n' "$*" >&2
    exit 64
    ;;
esac
EOF
cat >"$test_root/bin/timeout" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
while [[ "${1:-}" == --* ]]; do
  shift
done
: "${1:?timeout duration is required}"
shift
exec "$@"
EOF
chmod +x "$test_root/bin/make" "$test_root/bin/timeout"

case "$(uname -s)" in
  Darwin) build_cores="$(/usr/sbin/sysctl -n hw.logicalcpu)" ;;
  Linux) build_cores="$(getconf _NPROCESSORS_ONLN)" ;;
  *) exit 64 ;;
esac

PATH="$test_root/bin:$PATH" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT="$checkpoint_root" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  "$repo_root/tools/ci/source_build_identity.sh" >/dev/null

PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_PREFIX="$prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT="$checkpoint_root" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  GERBIL_SRC="$source_checkout" \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$test_root/bootstrap-attempt.json" \
    "$repo_root/tools/ci/bootstrap_gerbil.sh" >/dev/null

receipt="$prefix/bootstrap.receipt.json"
jq -e \
  --arg source_ref "$source_ref" \
  '.schema == "gerbil-bazel.gerbil-bootstrap-receipt.v1" and
   .outcome == "ready" and
   .source_ref == $source_ref and
   .source_build_identity.schema == "gerbil-bazel.source-build-identity.v1" and
   .checkpoint == {
     restored: false,
     restoredBoundary: false,
     lastSafeBoundary: "tools"
   } and
   [.phases[].name] == ["source-prepare", "configure", "upstream-build", "install"] and
   ([.phases[].exit_code] | all(. == 0))' \
  "$receipt" >/dev/null
jq -e '
  .schema == "gerbil-bazel.gerbil-bootstrap-attempt.v2" and
  .outcome == "ready" and
  .lastPhase == "install" and
  .exitCode == 0 and
  .signal == false and
  .successReceiptPresent == true and
  .successReceiptValidated == true and
  .checkpoint == {
    restoreOutcome: "not-found",
    restoredBoundary: false,
    restoredBoundaryIndex: false,
    restoredGeneration: false,
    lastSafeBoundary: "tools",
    lastSafeBoundaryIndex: 10
  }
' "$test_root/bootstrap-attempt.json" >/dev/null
"$repo_root/tools/ci/source_build_checkpoint.sh" validate \
  "$checkpoint_root" \
  "$source_checkout" \
  "$prefix" \
  "$identity_receipt"
[[ "$(
  "$repo_root/tools/ci/source_build_checkpoint.sh" boundary \
    "$checkpoint_root" \
    "$source_checkout" \
    "$prefix" \
    "$identity_receipt"
)" == tools ]]
tools_generation="$(jq -er '.generation' "$checkpoint_root/current.json")"

rm -rf "$prefix"
PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_PREFIX="$prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT="$checkpoint_root" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  GERBIL_SRC="$source_checkout" \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$test_root/resumed-bootstrap-attempt.json" \
    "$repo_root/tools/ci/bootstrap_gerbil.sh" >/dev/null
jq -e '
  .outcome == "ready" and
  .checkpoint == {
    restored: true,
    restoredBoundary: "tools",
    lastSafeBoundary: "tools"
  }
' "$prefix/bootstrap.receipt.json" >/dev/null
jq -e \
  --arg generation "$tools_generation" \
  '
  .outcome == "ready" and
  .successReceiptPresent == true and
  .successReceiptValidated == true and
  .checkpoint == {
    restoreOutcome: "restored",
    restoredBoundary: "tools",
    restoredBoundaryIndex: 10,
    restoredGeneration: $generation,
    lastSafeBoundary: "tools",
    lastSafeBoundaryIndex: 10
  }
' "$test_root/resumed-bootstrap-attempt.json" >/dev/null
[[ "$(wc -l <"$source_checkout/.synthetic-stages" | tr -d ' ')" -eq 11 ]]

progressive_prefix="$test_root/progressive-prefix"
progressive_source="$test_root/progressive-source"
progressive_checkpoint="$test_root/progressive-checkpoint"
set +e
PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_PREFIX="$progressive_prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT="$progressive_checkpoint" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  GERBIL_SRC="$progressive_source" \
  GERBIL_SYNTHETIC_BUILD_EXIT=42 \
  GERBIL_SYNTHETIC_FAIL_STAGE=stdlib \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$test_root/progressive-failed-attempt.json" \
    "$repo_root/tools/ci/bootstrap_gerbil.sh" >/dev/null 2>&1
progressive_failure_status=$?
set -e
[[ "$progressive_failure_status" -eq 42 ]]
jq -e '
  .outcome == "failed" and
  .lastPhase == "upstream-build" and
  .exitCode == 42 and
  .successReceiptPresent == false and
  .checkpoint == {
    restoreOutcome: "not-found",
    restoredBoundary: false,
    restoredBoundaryIndex: false,
    restoredGeneration: false,
    lastSafeBoundary: "stage1",
    lastSafeBoundaryIndex: 4
  }
' "$test_root/progressive-failed-attempt.json" >/dev/null
[[ "$(
  "$repo_root/tools/ci/source_build_checkpoint.sh" boundary \
    "$progressive_checkpoint" \
    "$progressive_source" \
    "$progressive_prefix" \
    "$identity_receipt"
)" == stage1 ]]
progressive_stage1_generation="$(
  jq -er '.generation' "$progressive_checkpoint/current.json"
)"
mkdir -p "$progressive_source/build/lib/std"
printf 'unsafe interrupted stdlib output\n' \
  >"$progressive_source/build/lib/std/partial.scm"

PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_PREFIX="$progressive_prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT="$progressive_checkpoint" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  GERBIL_SRC="$progressive_source" \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$test_root/progressive-ready-attempt.json" \
    "$repo_root/tools/ci/bootstrap_gerbil.sh" >/dev/null
jq -e '
  .outcome == "ready" and
  .checkpoint == {
    restored: true,
    restoredBoundary: "stage1",
    lastSafeBoundary: "tools"
  }
' "$progressive_prefix/bootstrap.receipt.json" >/dev/null
jq -e \
  --arg generation "$progressive_stage1_generation" \
  '
  .outcome == "ready" and
  .checkpoint == {
    restoreOutcome: "restored",
    restoredBoundary: "stage1",
    restoredBoundaryIndex: 4,
    restoredGeneration: $generation,
    lastSafeBoundary: "tools",
    lastSafeBoundaryIndex: 10
  }
' "$test_root/progressive-ready-attempt.json" >/dev/null
[[ ! -e "$progressive_source/build/lib/std/partial.scm" ]]
expected_stages="$(printf '%s\n' \
  prepare gambit boot-gxi stage0 stage1 stdlib libgerbil lang r7rs-large srfi tools)"
observed_stages="$(<"$progressive_source/.synthetic-stages")"
[[ "$observed_stages" == "$expected_stages" ]]

failure_prefix="$test_root/failure-prefix"
failure_source_checkout="$test_root/failure-source"
failure_progress="$test_root/failure-progress.json"
set +e
PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_BOOTSTRAP_PROGRESS_RECEIPT="$failure_progress" \
  GERBIL_PREFIX="$failure_prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  GERBIL_SRC="$failure_source_checkout" \
  GERBIL_SYNTHETIC_BUILD_EXIT=42 \
  "$repo_root/tools/ci/bootstrap_gerbil.sh" >/dev/null 2>&1
failure_status=$?
set -e
if [[ "$failure_status" -ne 42 ]]; then
  printf 'bootstrap did not preserve failed phase status: %s\n' "$failure_status" >&2
  exit 1
fi
if [[ -f "$failure_prefix/bootstrap.receipt.json" ]]; then
  printf 'failed bootstrap manufactured an immutable ready receipt\n' >&2
  exit 1
fi
jq -e '
  .phase == "upstream-build" and
  .state == "failed" and
  .exit_code == 42 and
  .checkpoint == {
    restoreOutcome: "not-configured",
    restoredBoundary: false,
    restoredBoundaryIndex: false,
    restoredGeneration: false,
    lastSafeBoundary: false,
    lastSafeBoundaryIndex: false
  }
' "$failure_progress" >/dev/null

shopt -s nullglob
temporary_bootstrap_receipts=(
  "$prefix"/.bootstrap.receipt.json.tmp.*
  "$failure_prefix"/.bootstrap.receipt.json.tmp.*
)
if (( ${#temporary_bootstrap_receipts[@]} != 0 )); then
  printf 'bootstrap left temporary immutable receipt files\n' >&2
  exit 1
fi
