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
json_validator=${14}
resource_guard=${15}
receipt_writer=${16}
process_guard=${17}
process_guard_timeout_seconds=${18}
package_identity=${19}
package_revision=${20}
shift 20

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
case "$json_validator" in /*) ;; *) json_validator="$PWD/$json_validator" ;; esac

case "$resource_guard" in
  /*) ;;
  *) resource_guard="$PWD/$resource_guard" ;;
esac
case "$receipt_writer" in
  /*) ;;
  *) receipt_writer="$PWD/$receipt_writer" ;;
esac

case "$process_guard" in
  0 | 1) ;;
  *)
    printf 'process guard flag must be 0 or 1, got %s\n' "$process_guard" >&2
    exit 64
    ;;
esac
case "$process_guard_timeout_seconds" in
  '' | *[!0-9]*)
    printf 'process guard timeout must be a non-negative integer, got %s\n' \
      "$process_guard_timeout_seconds" >&2
    exit 64
    ;;
esac

case "$build_script" in
  ''|/*|..|../*|*/../*|*/..)
    printf 'invalid staged build script path: %s\n' "$build_script" >&2
    exit 64
    ;;
esac

mkdir -p "$project_root"
staged_paths="$project_root/.gerbil-bazel-staged-paths"
: >"$staged_paths"
while IFS=$'\t' read -r source relative; do
  [[ -n "$source" ]] || continue
  case "$source" in /*) ;; *) source="$PWD/$source" ;; esac
  case "$relative" in
    ''|/*|..|../*|*/../*|*/..)
      printf 'invalid staged project source path: %s\n' "$relative" >&2
      exit 64
      ;;
  esac
  if grep -Fx "$relative" "$staged_paths" >/dev/null; then
    printf 'duplicate staged project source path: %s\n' "$relative" >&2
    exit 64
  fi
  printf '%s\n' "$relative" >>"$staged_paths"
  destination="$project_root/$relative"
  mkdir -p "$(dirname "$destination")"
  cp -pL "$source" "$destination"
  chmod u+w "$destination"
done < "$manifest"
rm -f "$staged_paths"

staged_build_script="$project_root/$build_script"
if [[ ! -f "$staged_build_script" ]]; then
  printf 'staged build script is missing: %s\n' "$build_script" >&2
  exit 66
fi
build_source_root=$(dirname "$staged_build_script")

export GERBIL_PATH="$project_root/.gerbil"
mkdir -p "$GERBIL_PATH/lib"
dependency_root=$(dirname "$dependency_root_marker")
project_dependency_loadpath=
if [[ -n ${GERBIL_BAZEL_PROJECT_DEPENDENCY_ROOTS:-} ]]; then
  IFS=: read -r -a project_dependency_roots \
    <<<"$GERBIL_BAZEL_PROJECT_DEPENDENCY_ROOTS"
  for dependency_project_root in "${project_dependency_roots[@]}"; do
    case "$dependency_project_root" in
      /*) ;;
      *) dependency_project_root="$PWD/$dependency_project_root" ;;
    esac
    dependency_library_root="$dependency_project_root/.gerbil/lib"
    if [[ ! -d "$dependency_library_root" ]]; then
      printf 'Gerbil project dependency library root is missing: %s\n' \
        "$dependency_library_root" >&2
      exit 66
    fi
    project_dependency_loadpath="$project_dependency_loadpath:$dependency_library_root"
  done
fi
export GERBIL_LOADPATH="$GERBIL_PATH/lib$project_dependency_loadpath:$dependency_root"

tool_bin="$project_root/.gerbil-tool-bin"
mkdir -p "$tool_bin"
ln -s "$gxi" "$tool_bin/gxi"
ln -s "$gxc" "$tool_bin/gxc"
ln -s "$gxpkg" "$tool_bin/gxpkg"
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
guard_receipt="$project_root/.gerbil-bazel-resource-guard.json"
if [[ "$process_guard" == 1 ]]; then
  (
    cd "$build_source_root"
    "$gxi" "$resource_guard" \
      "$guard_receipt" \
      "$package_identity@$package_revision" \
      "$process_guard_timeout_seconds" \
      "$gxi" "$staged_build_script" "$@"
  ) >"$log" 2>&1
else
  (
    cd "$build_source_root"
    "$gxi" "$staged_build_script" "$@"
  ) >"$log" 2>&1
fi
status=$?
set -e
finished_at=$(date +%s)

if (( status != 0 )); then
  printf 'Gerbil project build failed with exit %d; final log follows\n' "$status" >&2
  tail -n 200 "$log" >&2
  exit "$status"
fi

library_output_required=${GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT:-0}
case "$library_output_required" in
  0) ;;
  1)
    if ! find "$GERBIL_PATH/lib" -mindepth 1 -type f -print -quit | grep -q .; then
      printf 'Gerbil package build produced no library files: %s\n' \
        "$GERBIL_PATH/lib" >&2
      exit 66
    fi
    ;;
  *)
    printf 'GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT must be 0 or 1, got %s\n' \
      "$library_output_required" >&2
    exit 64
    ;;
esac

build_receipt_path=-
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
  build_receipt_path="$project_root/.gerbil-bazel-build-receipt.json"
  printf '%s\n' "$receipt_payload" >"$build_receipt_path"
else
  if [[ "$process_guard" == 0 ]]; then
    printf '{"durationSeconds":%d,"libraryOutputRequired":%s,"packageIdentity":%s,"packageRevision":%s,"schema":"gerbil-bazel.project-receipt.v1","status":"ok"}\n' \
      "$((finished_at - started_at))" \
      "$(if [[ "$library_output_required" == 1 ]]; then printf true; else printf false; fi)" \
      "${GERBIL_BAZEL_PACKAGE_IDENTITY_JSON:-\"\"}" \
      "${GERBIL_BAZEL_PACKAGE_REVISION_JSON:-\"\"}" \
      >"$receipt"
  fi
fi

resource_guard_path=-
if [[ "$process_guard" == 1 ]]; then
  resource_guard_path=$guard_receipt
fi

if [[ "$process_guard" == 1 || "$build_receipt_path" != - ]]; then
  set +e
  "$gxi" "$receipt_writer" \
    "$receipt" \
    "$((finished_at - started_at))" \
    "$library_output_required" \
    "${GERBIL_BAZEL_PACKAGE_IDENTITY_JSON:-\"\"}" \
    "${GERBIL_BAZEL_PACKAGE_REVISION_JSON:-\"\"}" \
    "$resource_guard_path" \
    "$build_receipt_path" \
    ok \
    >>"$log" 2>&1
  receipt_writer_status=$?
  set -e
  if ((receipt_writer_status != 0)); then
    printf 'Gerbil project receipt envelope could not be generated\n' >&2
    tail -n 200 "$log" >&2
    exit 66
  fi
fi

set +e
"$gxi" "$json_validator" "$receipt" >>"$log" 2>&1
validation_status=$?
set -e
if (( validation_status != 0 )); then
  printf 'Gerbil project receipt is not exactly one valid JSON value\n' >&2
  tail -n 200 "$log" >&2
  exit 66
fi
