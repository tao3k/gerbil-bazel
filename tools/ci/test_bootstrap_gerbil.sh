#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
upstream="$test_root/upstream"
prefix="$test_root/prefix"
source_checkout="$test_root/source"
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
EOF
chmod +x "$upstream/configure"
git -C "$upstream" init --quiet
git -C "$upstream" add configure
git -C "$upstream" \
  -c user.name=gerbil-bazel \
  -c user.email=gerbil-bazel@example.invalid \
  commit --quiet -m fixture
source_ref="$(git -C "$upstream" rev-parse HEAD)"

cat >"$test_root/bin/make" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  -j*)
    if [[ "${GERBIL_SYNTHETIC_BUILD_EXIT:-0}" -ne 0 ]]; then
      exit "$GERBIL_SYNTHETIC_BUILD_EXIT"
    fi
    mkdir -p .synthetic-build
    cat >.synthetic-build/gxi <<'INNER'
#!/usr/bin/env bash
printf 'Gerbil synthetic-bootstrap-test\n'
INNER
    chmod +x .synthetic-build/gxi
    ;;
  install)
    prefix="$(<.synthetic-prefix)"
    mkdir -p "$prefix/bin"
    cp .synthetic-build/gxi "$prefix/bin/gxi"
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
  GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT="$identity_receipt" \
  "$repo_root/tools/ci/source_build_identity.sh" >/dev/null

PATH="$test_root/bin:$PATH" \
  GERBIL_BUILD_CORES="$build_cores" \
  GERBIL_PREFIX="$prefix" \
  GERBIL_REF="$source_ref" \
  GERBIL_SOURCE_URL="$upstream" \
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
   [.phases[].name] == ["source-prepare", "configure", "upstream-build", "install"] and
   ([.phases[].exit_code] | all(. == 0))' \
  "$receipt" >/dev/null
jq -e '
  .schema == "gerbil-bazel.gerbil-bootstrap-attempt.v1" and
  .outcome == "ready" and
  .lastPhase == "install" and
  .exitCode == 0 and
  .signal == false and
  .successReceiptPresent == true and
  .successReceiptValidated == true
' "$test_root/bootstrap-attempt.json" >/dev/null

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
  .exit_code == 42
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
