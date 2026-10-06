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
patch_dir="$root/patches/gerbil-v19-darwin"
gerbil_patches=(patches/gerbil-v19-bio-integer-growth-upstream.patch)
gambit_patches=()
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
  )
  gambit_patches=(
    0001-gambit-darwin-posix-spawn.patch
    0004-gambit-darwin-gcc-macro-expansion.patch
    0015-gambit-darwin-literal-build-substitution.patch
  )
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
  for patch in "${gambit_patches[@]}"; do sha256_file "$patch_dir/$patch"; done
  sha256_file "$root/tools/ci/build_source_toolchain.sh"
  sha256_file "$root/tools/release/activate-gerbil.sh"
} | shasum -a 256 | awk '{print $1}')"
identity="$GERBIL_SOURCE_REVISION-$GAMBIT_SOURCE_REVISION-$compiler_hash-$patchset_hash"

verify() {
  jq -e --arg identity "$identity" '.identity == $identity and .multipleVms == true' \
    "$GERBIL_PREFIX/ci-source-toolchain.json" >/dev/null
  source "$GERBIL_PREFIX/activate"
  grep -Eq '^#define ___MULTIPLE_VMS([[:space:]]|$)' "$GERBIL_HOME/include/gambit.h"
  "$GERBIL_PREFIX/bin/gxi" -v 2>&1 | grep -F "Gerbil ${GERBIL_SOURCE_REVISION:0:7}"
  if [[ "$platform" == Darwin ]]; then
    grep -F 'replace_literal()' "$GERBIL_HOME/bin/gambuild-C"
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
      git -C "$source_dir/src/gambit" apply --check "$patch_dir/$patch"
    done
    printf 'cache_identity=%s\n' "$identity" >> "${GITHUB_OUTPUT:?}"
    ;;
  build)
    [[ "$(git -C "$source_dir" rev-parse HEAD)" == "$GERBIL_SOURCE_REVISION" ]]
    unset GERBIL_HOME GERBIL_LOADPATH GERBIL_GSC GAMBOPT GERBIL_BUILD_PREFIX
    export GERBIL_PATH="$source_dir/ci-gerbil-path"
    export CFLAGS="-pipe${CFLAGS:+ $CFLAGS}"
    args=("--prefix=$GERBIL_PREFIX" "--with-gambit=$GAMBIT_SOURCE_REVISION"
          "--version-string=${GERBIL_SOURCE_REVISION:0:7}" --enable-march=
          --enable-single-host=0 --enable-multiple-vms)
    if [[ "$platform" == Darwin ]]; then
      export GERBIL_BUILD_AOT_TOOLS=yes
      args+=(--enable-smp --enable-c-opt=-O1 --enable-c-opt-rts=yes --enable-gcc-opts
             --enable-inline-jumps --enable-dynamic-clib --enable-trust-c-tco)
    fi
    cd "$source_dir"
    ./configure "${args[@]}"
    [[ "$(git -C src/gambit rev-parse HEAD)" == "$GAMBIT_SOURCE_REVISION" ]]
    for patch in "${gambit_patches[@]}"; do
      git -C src/gambit apply "$patch_dir/$patch"
    done
    if [[ "$platform" == Darwin ]]; then
      touch src/gambit/configure
      (cd src/gambit && ./config.status --recheck && ./config.status)
      grep -F 'replace_literal()' src/gambit/bin/gambuild-C.unix
    fi
    grep -Eq '^#define ___MULTIPLE_VMS([[:space:]]|$)' src/gambit/include/gambit.h
    for target in prepare gambit boot-gxi stage0 stage1 stdlib libgerbil lang tools; do
      printf 'BUILD %s (%s cores)\n' "$target" "$cores"
      GERBIL_BUILD_FLAGS="-j$cores" ./build.sh "$target"
    done
    ./install.sh
    cp "$root/tools/release/activate-gerbil.sh" "$GERBIL_PREFIX/activate"
    jq -n --arg identity "$identity" --arg sourceRevision "$GERBIL_SOURCE_REVISION" \
      --arg gambitRevision "$GAMBIT_SOURCE_REVISION" --arg compilerHash "$compiler_hash" \
      --arg patchsetHash "$patchset_hash" --argjson cores "$cores" \
      '{identity:$identity, sourceRevision:$sourceRevision, gambitRevision:$gambitRevision,
        compilerHash:$compilerHash, patchsetHash:$patchsetHash, cores:$cores, multipleVms:true,
        scope:"source-toolchain-construction-not-D1510-performance-admission"}' \
      > "$GERBIL_PREFIX/ci-source-toolchain.json"
    verify
    ;;
  verify) verify ;;
  *) echo "usage: $0 prepare|build|verify" >&2; exit 64 ;;
esac
