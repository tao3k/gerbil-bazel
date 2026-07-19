#!/usr/bin/env bash
set -euo pipefail

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
receipt_line_prefix=${13}
shift 13

case "$gxi" in /*) ;; *) gxi="$PWD/$gxi" ;; esac
case "$gxc" in /*) ;; *) gxc="$PWD/$gxc" ;; esac
case "$gxpkg" in /*) ;; *) gxpkg="$PWD/$gxpkg" ;; esac
case "$gerbil_cc" in /*) ;; *) gerbil_cc="$PWD/$gerbil_cc" ;; esac
case "$gerbil_as" in /*) ;; *) gerbil_as="$PWD/$gerbil_as" ;; esac
case "$gerbil_ld" in /*) ;; *) gerbil_ld="$PWD/$gerbil_ld" ;; esac
case "$dependency_root_marker" in /*) ;; *) dependency_root_marker="$PWD/$dependency_root_marker" ;; esac
case "$manifest" in /*) ;; *) manifest="$PWD/$manifest" ;; esac
case "$project_root" in /*) ;; *) project_root="$PWD/$project_root" ;; esac
case "$receipt" in /*) ;; *) receipt="$PWD/$receipt" ;; esac
case "$log" in /*) ;; *) log="$PWD/$log" ;; esac

case "$build_script" in
  ''|/*|..|../*|*/../*|*/..)
    printf 'invalid staged build script path: %s\n' "$build_script" >&2
    exit 64
    ;;
esac

mkdir -p "$project_root"
while IFS=$'\t' read -r source relative; do
  [[ -n "$source" ]] || continue
  case "$source" in /*) ;; *) source="$PWD/$source" ;; esac
  case "$relative" in
    ''|/*|..|../*|*/../*|*/..)
      printf 'invalid staged project source path: %s\n' "$relative" >&2
      exit 64
      ;;
  esac
  destination="$project_root/$relative"
  mkdir -p "$(dirname "$destination")"
  cp -pL "$source" "$destination"
  chmod u+w "$destination"
done < "$manifest"

if [[ ! -f "$project_root/$build_script" ]]; then
  printf 'staged build script is missing: %s\n' "$build_script" >&2
  exit 66
fi

export GERBIL_PATH="$project_root/.gerbil"
mkdir -p "$GERBIL_PATH/lib"
dependency_root=$(dirname "$dependency_root_marker")
export GERBIL_LOADPATH="$GERBIL_PATH/lib:$dependency_root"

tool_bin="$project_root/.gerbil-tool-bin"
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

if [[ -n "$receipt_line_prefix" ]]; then
  receipt_payload=
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      "$receipt_line_prefix"*) receipt_payload=${line#"$receipt_line_prefix"} ;;
    esac
  done <"$log"
  if [[ -z "$receipt_payload" ]]; then
    printf 'Gerbil project build completed without receipt prefix %s\n' \
      "$receipt_line_prefix" >&2
    tail -n 200 "$log" >&2
    exit 65
  fi
  printf '%s\n' "$receipt_payload" >"$receipt"
else
  printf '{"durationSeconds":%d,"schema":"gerbil-bazel.project-receipt.v1","status":"ok"}\n' \
    "$((finished_at - started_at))" >"$receipt"
fi
