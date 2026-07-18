#!/usr/bin/env bash
set -euo pipefail

gxi=$1
manifest=$2
project_root=$3
build_script=$4
receipt=$5
shift 5

case "$gxi" in /*) ;; *) gxi="$PWD/$gxi" ;; esac
case "$manifest" in /*) ;; *) manifest="$PWD/$manifest" ;; esac
case "$project_root" in /*) ;; *) project_root="$PWD/$project_root" ;; esac
case "$receipt" in /*) ;; *) receipt="$PWD/$receipt" ;; esac

mkdir -p "$project_root"
while IFS=$'\t' read -r source relative; do
  [[ -n "$source" ]] || continue
  case "$source" in /*) ;; *) source="$PWD/$source" ;; esac
  destination="$project_root/$relative"
  mkdir -p "$(dirname "$destination")"
  cp -p "$source" "$destination"
done < "$manifest"

export GERBIL_PATH="$project_root/.gerbil"
mkdir -p "$GERBIL_PATH/lib"

started_at=$(date +%s)
(
  cd "$project_root"
  "$gxi" "$build_script" "$@"
)
finished_at=$(date +%s)

printf '{"durationSeconds":%d,"schema":"gerbil-bazel.project-receipt.v1","status":"ok"}\n' \
  "$((finished_at - started_at))" > "$receipt"
