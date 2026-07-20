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
chmod +x "$test_root/bin/make"

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
