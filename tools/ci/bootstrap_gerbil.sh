#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_REF:?GERBIL_REF is required}"
: "${GERBIL_PREFIX:?GERBIL_PREFIX is required}"
: "${GERBIL_SRC:?GERBIL_SRC is required}"

gerbil_source_url="${GERBIL_SOURCE_URL:-https://github.com/mighty-gerbils/gerbil.git}"
build_cores="${GERBIL_BUILD_CORES:-}"
require_ccache="${GERBIL_REQUIRE_CCACHE:-0}"
started_at="$SECONDS"

if [[ -z "$build_cores" ]]; then
  build_cores="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
fi
if [[ ! "$build_cores" =~ ^[1-9][0-9]*$ ]]; then
  printf 'could not determine positive available CPU count: %s\n' "$build_cores" >&2
  exit 64
fi

ccache_executable="$(command -v ccache || true)"
ccache_enabled=false
ccache_activity=0
compiler="${CC:-cc}"
if [[ -n "$ccache_executable" ]]; then
  ccache_enabled=true
  mkdir -p "${CCACHE_DIR:-$HOME/.cache/ccache}"
  "$ccache_executable" --set-config="max_size=${CCACHE_MAXSIZE:-2G}"
  "$ccache_executable" --zero-stats
  if [[ "$compiler" != ccache\ * && "$compiler" != "$ccache_executable"\ * ]]; then
    compiler="$ccache_executable $compiler"
  fi
elif [[ "$require_ccache" == 1 ]]; then
  printf 'ccache is required but was not discovered on PATH\n' >&2
  exit 69
fi
export CC="$compiler"

mkdir -p "$(dirname "$GERBIL_SRC")" "$(dirname "$GERBIL_PREFIX")"
rm -rf "$GERBIL_SRC" "$GERBIL_PREFIX"
git init --quiet "$GERBIL_SRC"
git -C "$GERBIL_SRC" remote add origin "$gerbil_source_url"
git -C "$GERBIL_SRC" fetch --depth=1 origin "$GERBIL_REF"
git -C "$GERBIL_SRC" checkout --quiet --detach FETCH_HEAD

(
  cd "$GERBIL_SRC"
  ./configure --prefix="$GERBIL_PREFIX" --enable-march=
  export GERBIL_BUILD_CORES="$build_cores"
  make -j"$build_cores"
  make install
)

if [[ "$ccache_enabled" == true ]]; then
  ccache_stats="$($ccache_executable --print-stats 2>/dev/null || true)"
  ccache_activity="$(
    printf '%s\n' "$ccache_stats" | awk '
      $1 == "cache_miss" ||
      $1 == "direct_cache_hit" ||
      $1 == "preprocessed_cache_hit" { total += $2 }
      END { print total + 0 }
    '
  )"
  "$ccache_executable" --show-stats
  if [[ "$require_ccache" == 1 && "$ccache_activity" -lt 1 ]]; then
    printf 'ccache was required but observed no compiler activity\n' >&2
    exit 70
  fi
fi

gerbil_version="$("$GERBIL_PREFIX/bin/gxi" --version)"
elapsed_seconds="$((SECONDS - started_at))"
jq -n \
  --arg schema gerbil-bazel.gerbil-bootstrap-receipt.v1 \
  --arg source_ref "$GERBIL_REF" \
  --arg source_url "$gerbil_source_url" \
  --arg prefix "$GERBIL_PREFIX" \
  --arg version "$gerbil_version" \
  --arg compiler "$compiler" \
  --argjson build_cores "$build_cores" \
  --argjson ccache_enabled "$ccache_enabled" \
  --argjson ccache_activity "$ccache_activity" \
  --argjson elapsed_seconds "$elapsed_seconds" \
  '{
    schema: $schema,
    outcome: "ready",
    source_ref: $source_ref,
    source_url: $source_url,
    prefix: $prefix,
    gerbil_version: $version,
    compiler: $compiler,
    build_cores: $build_cores,
    ccache: {
      enabled: $ccache_enabled,
      compiler_activity: $ccache_activity
    },
    elapsed_seconds: $elapsed_seconds
  }' >"$GERBIL_PREFIX/bootstrap.receipt.json"

jq -c . "$GERBIL_PREFIX/bootstrap.receipt.json"

