#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${GERBIL_SOURCE_REVISION:?exact Gerbil revision required}"
: "${GAMBIT_SOURCE_REVISION:?exact Gambit gitlink required}"
: "${GERBIL_SOURCE_DIRECTORY:?isolated source directory required}"
: "${GERBIL_PREFIX:?isolated install prefix required}"
[[ "$GERBIL_SOURCE_REVISION" =~ ^[0-9a-f]{40}$ ]]
[[ "$GAMBIT_SOURCE_REVISION" =~ ^[0-9a-f]{40}$ ]]
source_dir="$GERBIL_SOURCE_DIRECTORY"
platform="$(uname -s)"
gerbil_patches=(patches/gerbil-v19-bio-integer-growth-upstream.patch)
gambit_patches=(
  patches/gambit-v19-multiple-vms-global-capacity.patch
  patches/gambit-v19-multiple-vms-global-setup-state.patch
)
multiple_vms=true
if [[ "$platform" == Darwin ]]; then
  gerbil_patches+=(
    patches/gerbil-v19-ffi-release-pkey-once.patch
    patches/gerbil-v19-darwin-aot-tools.patch
    patches/gerbil-v19-darwin/0002-gerbil-streaming-compile-executor.patch
    patches/gerbil-v19-darwin/0003-gerbil-darwin-executable-closure-dag.patch
    patches/gerbil-v19-darwin/0007-gerbil-darwin-executable-runtime-object-reuse.patch
    patches/gerbil-v19-darwin/0008-gerbil-darwin-pure-module-original-path.patch
    patches/gerbil-v19-darwin/0010-gerbil-darwin-socket-address-contract.patch
    patches/gerbil-v19-darwin/0011-gerbil-darwin-release-dynamic-linkage.patch
    patches/gerbil-v19-darwin/static-reuse-helper-install.patch
  )
  gambit_patches+=(
    patches/gerbil-v19-darwin/0001-gambit-darwin-posix-spawn.patch
    patches/gerbil-v19-darwin/0004-gambit-darwin-gcc-macro-expansion.patch
  )
  # The locked series includes 0015-gambit-darwin-literal-build-substitution.patch.
  # Compile the snapshot helper here; reuse remains opt-in for consumers.
  python3 "$root/patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py" \
    "$root/patches/gerbil-v19-darwin/receipts/d1510-static-c-snapshot-patch-lock.json" \
    --lock-sha256 a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2 --performance
  while IFS= read -r patch; do
    gambit_patches+=("patches/gerbil-v19-darwin/$patch")
  done < "$root/patches/gerbil-v19-darwin/static-c-snapshot-candidate.series"
  gambit_patches+=(patches/gerbil-v19-darwin/static-snapshot-path-fallback.patch)
fi

sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }
compiler="${CC:-gcc}"
compiler="$(command -v "$compiler")"
macros="$("$compiler" -dM -E -x c /dev/null)"
grep -q '__GNUC__' <<< "$macros"
if grep -q '__clang__' <<< "$macros"; then
  echo 'source CI requires GNU GCC, not clang' >&2
  exit 1
fi
if [[ "$platform" == Darwin ]]; then
  grep -Eq '^#define __GNUC__ 16$' <<< "$macros"
  cores="$(sysctl -n hw.physicalcpu)"
else
  [[ "$platform" == Linux ]]
  cores="$(getconf _NPROCESSORS_ONLN)"
fi
[[ "$cores" =~ ^[1-9][0-9]*$ ]]
export CC="$compiler" GERBIL_GCC="$compiler" GERBIL_BUILD_CORES="$cores"
compiler_hash="$(sha256_file "$compiler")"
patchset_hash="$({
  for patch in "${gerbil_patches[@]}"; do sha256_file "$root/$patch"; done
  for patch in "${gambit_patches[@]}"; do sha256_file "$root/$patch"; done
  sha256_file "$root/tools/ci/build_source_toolchain.sh"
  sha256_file "$root/tools/release/activate-gerbil.sh"
} | shasum -a 256 | awk '{print $1}')"
identity="$GERBIL_SOURCE_REVISION-$GAMBIT_SOURCE_REVISION-$compiler_hash-$patchset_hash"

verify() {
  jq -e --arg identity "$identity" --argjson multipleVms "$multiple_vms" \
    '.identity == $identity and .multipleVms == $multipleVms' \
    "$GERBIL_PREFIX/ci-source-toolchain.json" >/dev/null
  source "$GERBIL_PREFIX/activate"
  "$GERBIL_PREFIX/bin/gxi" -v 2>&1 | grep -F "Gerbil ${GERBIL_SOURCE_REVISION:0:7}"
  grep -Eq '^#define ___MULTIPLE_VMS([[:space:]]|$)' "$GERBIL_HOME/include/gambit.h"
  if [[ "$platform" == Darwin ]]; then
    grep -F 'replace_literal()' "$GERBIL_HOME/bin/gambuild-C"
    test -x "$GERBIL_HOME/bin/gambit-file-sha256"
    test ! -L "$GERBIL_HOME/bin/gambit-file-sha256"
    grep -F 'bound_input_sha=' "$GERBIL_HOME/bin/gambit-static-object-reuse"
  fi
  mkdir -p "$root/.ci/receipts"
  cp "$GERBIL_PREFIX/ci-source-toolchain.json" "$root/.ci/receipts/source-toolchain.json"
}

case "${1:-}" in
  prepare)
    [[ ! -e "$source_dir" ]]
    git init "$source_dir"
    git -C "$source_dir" remote add origin https://git.cons.io/mighty-gerbils/gerbil.git
    git -C "$source_dir" fetch --depth=256 origin "$GERBIL_SOURCE_REVISION"
    [[ "$(git -C "$source_dir" rev-parse FETCH_HEAD)" == "$GERBIL_SOURCE_REVISION" ]]
    git -C "$source_dir" checkout --detach "$GERBIL_SOURCE_REVISION"
    git -C "$source_dir" submodule update --init --depth=1
    [[ "$(git -C "$source_dir/src/gambit" rev-parse HEAD)" == "$GAMBIT_SOURCE_REVISION" ]]
    for patch in "${gerbil_patches[@]}"; do
      git -C "$source_dir" apply "$root/$patch"
    done
    for patch in "${gambit_patches[@]}"; do
      git -C "$source_dir/src/gambit" apply --check "$root/$patch"
      git -C "$source_dir/src/gambit" apply "$root/$patch"
    done
    # Dependent patches must be checked in composition, then restored before
    # configure selects the pinned submodule and the build applies them again.
    for ((index=${#gambit_patches[@]}-1; index>=0; index--)); do
      git -C "$source_dir/src/gambit" apply --reverse "$root/${gambit_patches[index]}"
    done
    git -C "$source_dir/src/gambit" diff --exit-code
    printf 'cache_identity=%s\n' "$identity" >> "${GITHUB_OUTPUT:?}"
    ;;
  build)
    [[ "$(git -C "$source_dir" rev-parse HEAD)" == "$GERBIL_SOURCE_REVISION" ]]
    unset GERBIL_HOME GERBIL_LOADPATH GERBIL_GSC GAMBOPT GERBIL_BUILD_PREFIX
    export GERBIL_PATH="$source_dir/ci-gerbil-path"
    export CFLAGS="-pipe${CFLAGS:+ $CFLAGS}"
    args=("--prefix=$GERBIL_PREFIX" "--with-gambit=$GAMBIT_SOURCE_REVISION"
          "--version-string=${GERBIL_SOURCE_REVISION:0:7}" --enable-march=
          --enable-single-host=0 --enable-multiple-vms --enable-smp)
    if [[ "$platform" == Darwin ]]; then
      export GERBIL_BUILD_AOT_TOOLS=yes
      args+=(--enable-c-opt=-O1 --enable-c-opt-rts=yes --enable-gcc-opts
             --enable-inline-jumps --enable-dynamic-clib --enable-trust-c-tco)
    fi
    cd "$source_dir"
    ./configure "${args[@]}"
    [[ "$(git -C src/gambit rev-parse HEAD)" == "$GAMBIT_SOURCE_REVISION" ]]
    for patch in "${gambit_patches[@]}"; do
      git -C src/gambit apply "$root/$patch"
    done
    if [[ "$platform" == Darwin ]]; then
      touch src/gambit/configure
      (cd src/gambit && ./config.status --recheck && ./config.status)
      grep -F 'replace_literal()' src/gambit/bin/gambuild-C.unix
    else
      (cd src/gambit && ./config.status)
    fi
    grep -Eq '^#define ___MULTIPLE_VMS([[:space:]]|$)' src/gambit/include/gambit.h
    for target in prepare gambit boot-gxi stage0 stage1 stdlib libgerbil lang tools; do
      printf 'BUILD %s (%s cores)\n' "$target" "$cores"
      GERBIL_BUILD_FLAGS="-j$cores" ./build.sh "$target"
      if [[ "$target" == gambit ]]; then
        # Upstream's Gambit wrapper can return zero after a make failure.
        if [[ ! -x build/bin/gsc || ! -x bootstrap/bin/gsi || ! -f build/lib/libgambit.a ]]; then
          echo 'Gambit build missing build/bin/gsc, bootstrap/bin/gsi or build/lib/libgambit.a' >&2
          exit 1
        fi
        build/bin/gsc -v
        bootstrap/bin/gsi -v
      fi
    done
    ./install.sh
    cp "$root/tools/release/activate-gerbil.sh" "$GERBIL_PREFIX/activate"
    jq -n --arg identity "$identity" --arg sourceRevision "$GERBIL_SOURCE_REVISION" \
      --arg gambitRevision "$GAMBIT_SOURCE_REVISION" --arg compilerHash "$compiler_hash" \
      --arg patchsetHash "$patchset_hash" --argjson cores "$cores" --argjson multipleVms "$multiple_vms" \
      '{identity:$identity, sourceRevision:$sourceRevision, gambitRevision:$gambitRevision,
        compilerHash:$compilerHash, patchsetHash:$patchsetHash, cores:$cores, multipleVms:$multipleVms,
        scope:"source-toolchain-construction-not-D1510-performance-admission"}' \
      > "$GERBIL_PREFIX/ci-source-toolchain.json"
    verify
    ;;
  verify) verify ;;
  *) echo "usage: $0 prepare|build|verify" >&2; exit 64 ;;
esac
