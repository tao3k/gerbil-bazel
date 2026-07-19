#!/usr/bin/env bash
set -euo pipefail

if (( $# < 13 )); then
  printf 'usage: %s GXI GXC GXPKG CC AS LD DEPENDENCY_ROOT_MARKER MANIFEST PROJECT_ROOT BUILD_SS RECEIPT LOG RECEIPT_PREFIX [BUILD_ARGS...]\n' "$0" >&2
  exit 64
fi

gxi=$1
gxc=$2
gxpkg=$3
gerbil_cc=$4
gerbil_as=$5
gerbil_ld=$6
dependency_root_marker=$7
manifest=$8
project_root=$9
build_script=${10}
receipt=${11}
log=${12}
receipt_prefix=${13}
shift 13

absolute_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$PWD" "$1" ;;
  esac
}

gxi=$(absolute_path "$gxi")
gxc=$(absolute_path "$gxc")
gxpkg=$(absolute_path "$gxpkg")
gerbil_cc=$(absolute_path "$gerbil_cc")
gerbil_as=$(absolute_path "$gerbil_as")
gerbil_ld=$(absolute_path "$gerbil_ld")
dependency_root_marker=$(absolute_path "$dependency_root_marker")
manifest=$(absolute_path "$manifest")
project_root=$(absolute_path "$project_root")
receipt=$(absolute_path "$receipt")
log=$(absolute_path "$log")

mkdir -p "$project_root"
while IFS=$'\t' read -r source relative; do
  [[ -n "$source" ]] || continue
  source=$(absolute_path "$source")
  case "/$relative/" in
    */../*|*/./*|//* )
      printf 'unsafe staged source path: %s\n' "$relative" >&2
      exit 65
      ;;
  esac
  destination="$project_root/$relative"
  mkdir -p "$(dirname "$destination")"
  cp -p "$source" "$destination"
done < "$manifest"

export GERBIL_PATH="$project_root/.gerbil"
dependency_root=$(dirname "$dependency_root_marker")
export GERBIL_LOADPATH="$GERBIL_PATH/lib:$dependency_root"
mkdir -p "$GERBIL_PATH/lib"

tool_bin="$project_root/.gerbil-bazel-tool-bin"
mkdir -p "$tool_bin"
ln -s "$gxi" "$tool_bin/gxi"
ln -s "$gxc" "$tool_bin/gxc"
ln -s "$gxpkg" "$tool_bin/gxpkg"
ln -s "$gerbil_cc" "$tool_bin/gcc-16"
ln -s "$gerbil_cc" "$tool_bin/cc"
ln -s "$gerbil_as" "$tool_bin/as"
ln -s "$gerbil_ld" "$tool_bin/ld"
export CC="$gerbil_cc"
export PATH="$tool_bin:$PATH"

cleanup_tool_bin() {
  rm -rf "$tool_bin"
}
trap cleanup_tool_bin EXIT

started_at=$(date +%s)
set +e
(
  cd "$project_root"
  "$gxi" "$build_script" "$@"
) >"$log" 2>&1
status=$?
set -e
finished_at=$(date +%s)

if (( status != 0 )); then
  printf 'Gerbil project build failed with exit %d; final log follows\n' "$status" >&2
  tail -n 200 "$log" >&2
  exit "$status"
fi

if [[ -n "$receipt_prefix" ]]; then
  receipt_payload=
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      "$receipt_prefix"*) receipt_payload=${line#"$receipt_prefix"} ;;
    esac
  done < "$log"
  if [[ -z "$receipt_payload" ]]; then
    printf 'Gerbil project build completed without the declared JSON receipt prefix: %s\n' "$receipt_prefix" >&2
    tail -n 200 "$log" >&2
    exit 66
  fi
  printf '%s\n' "$receipt_payload" > "$receipt"
else
  printf '{"durationSeconds":%d,"schema":"gerbil-bazel.project-receipt.v1","status":"ok"}\n' \
    "$((finished_at - started_at))" > "$receipt"
fi
