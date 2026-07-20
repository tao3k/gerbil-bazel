#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_REF:?GERBIL_REF is required}"
: "${GERBIL_PREFIX:?GERBIL_PREFIX is required}"
: "${GERBIL_SRC:?GERBIL_SRC is required}"

gerbil_source_url="${GERBIL_SOURCE_URL:-https://github.com/mighty-gerbils/gerbil.git}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source_build_config="${GERBIL_SOURCE_BUILD_CONFIG:-$repo_root/tools/ci/gerbil_source_build_config.json}"
source_build_identity_receipt="${GERBIL_SOURCE_BUILD_IDENTITY_RECEIPT:-}"
build_cores="${GERBIL_BUILD_CORES:-}"
require_ccache="${GERBIL_REQUIRE_CCACHE:-0}"
started_at="$SECONDS"
phases='[]'
progress_receipt="${GERBIL_BOOTSTRAP_PROGRESS_RECEIPT:-}"

write_progress() {
  local phase=$1
  local state=$2
  local exit_code=${3:-false}
  local progress_dir
  local progress_name
  local progress_tmp
  if [[ -z "$progress_receipt" ]]; then
    return
  fi
  progress_dir="$(dirname "$progress_receipt")"
  progress_name="$(basename "$progress_receipt")"
  mkdir -p "$progress_dir"
  progress_tmp="$(mktemp "$progress_dir/.$progress_name.tmp.XXXXXX")"
  if ! jq -n \
    --arg phase "$phase" \
    --arg state "$state" \
    --argjson exit_code "$exit_code" \
    '{phase: $phase, state: $state, exit_code: $exit_code}' \
    >"$progress_tmp"; then
    rm -f "$progress_tmp"
    return 1
  fi
  mv "$progress_tmp" "$progress_receipt"
}

source_build_config_json="$(
  jq -cSe '
    select(.schema == "gerbil-bazel.source-build-config.v1") |
    select(.contractVersion == 1) |
    select(.outputIdentity.configureArguments | type == "array") |
    select(.outputIdentity.upstreamEntrypoints == {
      configure: "./configure",
      build: "make",
      install: "make install"
    }) |
    select(.executionPolicy.parallelism == {
      source: "available-logical-cpus",
      makeArgument: "-j"
    }) |
    select(.executionPolicy.compilerCache.tool == "ccache")
  ' "$source_build_config"
)"
configure_arguments=()
while IFS= read -r argument; do
  configure_arguments+=("$argument")
done < <(jq -er '.outputIdentity.configureArguments[]' <<<"$source_build_config_json")
configured_ccache_max_size="$(
  jq -er '.executionPolicy.compilerCache.maxSize' <<<"$source_build_config_json"
)"

source_build_identity=null
if [[ -n "$source_build_identity_receipt" ]]; then
  jq -e \
    --arg source_ref "$GERBIL_REF" \
    --argjson config "$source_build_config_json" \
    '.schema == "gerbil-bazel.source-build-identity.v1" and
     .source.ref == $source_ref and
     .config.value == $config' \
    "$source_build_identity_receipt" >/dev/null
  source_build_identity="$(jq -cS . "$source_build_identity_receipt")"
fi

run_phase() {
  local name=$1
  shift
  local phase_started_at=$SECONDS
  local exit_code
  write_progress "$name" running false
  set +e
  "$@"
  exit_code=$?
  set -e
  phases="$(
    jq -cn \
      --argjson phases "$phases" \
      --arg name "$name" \
      --argjson exit_code "$exit_code" \
      --argjson elapsed_seconds "$((SECONDS - phase_started_at))" \
      '$phases + [{
        name: $name,
        exit_code: $exit_code,
        elapsed_seconds: $elapsed_seconds
      }]'
  )"
  if [[ "$exit_code" -ne 0 ]]; then
    write_progress "$name" failed "$exit_code" || true
    printf 'Gerbil source build phase failed: %s (exit %s)\n' \
      "$name" "$exit_code" >&2
    exit "$exit_code"
  fi
  write_progress "$name" completed "$exit_code"
}

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
ccache_direct_hits=0
ccache_preprocessed_hits=0
ccache_misses=0
compiler="${CC:-cc}"
if [[ -n "$ccache_executable" ]]; then
  ccache_enabled=true
  mkdir -p "${CCACHE_DIR:-$HOME/.cache/ccache}"
  "$ccache_executable" --set-config="max_size=${CCACHE_MAXSIZE:-$configured_ccache_max_size}"
  "$ccache_executable" --zero-stats
  if [[ "$compiler" != ccache\ * && "$compiler" != "$ccache_executable"\ * ]]; then
    compiler="$ccache_executable $compiler"
  fi
elif [[ "$require_ccache" == 1 ]]; then
  printf 'ccache is required but was not discovered on PATH\n' >&2
  exit 69
fi
export CC="$compiler"

prepare_source() {
  mkdir -p "$(dirname "$GERBIL_SRC")" "$(dirname "$GERBIL_PREFIX")" || return
  rm -rf "$GERBIL_SRC" "$GERBIL_PREFIX" || return
  git init --quiet "$GERBIL_SRC" || return
  git -C "$GERBIL_SRC" remote add origin "$gerbil_source_url" || return
  git -C "$GERBIL_SRC" fetch --depth=1 origin "$GERBIL_REF" || return
  git -C "$GERBIL_SRC" checkout --quiet --detach FETCH_HEAD
}

configure_source() {
  cd "$GERBIL_SRC" || return
  ./configure --prefix="$GERBIL_PREFIX" "${configure_arguments[@]}"
}

build_source() {
  cd "$GERBIL_SRC" || return
  export GERBIL_BUILD_CORES="$build_cores"
  make -j"$build_cores"
}

install_source() {
  cd "$GERBIL_SRC" || return
  make install
}

run_phase source-prepare prepare_source
run_phase configure configure_source
run_phase upstream-build build_source
run_phase install install_source

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
  ccache_direct_hits="$(
    printf '%s\n' "$ccache_stats" | awk '$1 == "direct_cache_hit" { print $2 + 0 }'
  )"
  ccache_preprocessed_hits="$(
    printf '%s\n' "$ccache_stats" | awk '$1 == "preprocessed_cache_hit" { print $2 + 0 }'
  )"
  ccache_misses="$(
    printf '%s\n' "$ccache_stats" | awk '$1 == "cache_miss" { print $2 + 0 }'
  )"
  ccache_direct_hits="${ccache_direct_hits:-0}"
  ccache_preprocessed_hits="${ccache_preprocessed_hits:-0}"
  ccache_misses="${ccache_misses:-0}"
  "$ccache_executable" --show-stats
  if [[ "$require_ccache" == 1 && "$ccache_activity" -lt 1 ]]; then
    printf 'ccache was required but observed no compiler activity\n' >&2
    exit 70
  fi
fi

gerbil_version="$("$GERBIL_PREFIX/bin/gxi" --version)"
elapsed_seconds="$((SECONDS - started_at))"
bootstrap_receipt="$GERBIL_PREFIX/bootstrap.receipt.json"
bootstrap_receipt_tmp="$(mktemp "$GERBIL_PREFIX/.bootstrap.receipt.json.tmp.XXXXXX")"
if ! jq -n \
  --arg schema gerbil-bazel.gerbil-bootstrap-receipt.v1 \
  --arg source_ref "$GERBIL_REF" \
  --arg source_url "$gerbil_source_url" \
  --arg prefix "$GERBIL_PREFIX" \
  --arg version "$gerbil_version" \
  --arg compiler "$compiler" \
  --argjson build_cores "$build_cores" \
  --argjson ccache_enabled "$ccache_enabled" \
  --argjson ccache_activity "$ccache_activity" \
  --argjson ccache_direct_hits "$ccache_direct_hits" \
  --argjson ccache_preprocessed_hits "$ccache_preprocessed_hits" \
  --argjson ccache_misses "$ccache_misses" \
  --argjson elapsed_seconds "$elapsed_seconds" \
  --argjson phases "$phases" \
  --argjson source_build_identity "$source_build_identity" \
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
      compiler_activity: $ccache_activity,
      direct_hits: $ccache_direct_hits,
      preprocessed_hits: $ccache_preprocessed_hits,
      misses: $ccache_misses
    },
    elapsed_seconds: $elapsed_seconds,
    phases: $phases,
    source_build_identity: $source_build_identity
  }' >"$bootstrap_receipt_tmp"; then
  rm -f "$bootstrap_receipt_tmp"
  exit 1
fi
mv "$bootstrap_receipt_tmp" "$bootstrap_receipt"

jq -c . "$bootstrap_receipt"
