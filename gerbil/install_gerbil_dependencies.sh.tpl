#!/usr/bin/env bash
set -euo pipefail

workspace=${BUILD_WORKSPACE_DIRECTORY:?BUILD_WORKSPACE_DIRECTORY is required}
gerbil_root=${GERBIL_PATH:-"$workspace/.gerbil"}
gxi={{GXI}}
gxpkg={{GXPKG}}
resource_guard={{RESOURCE_GUARD}}
native_environment=({{NATIVE_ENVIRONMENT_ARGS}})
phase=initialize

report_failure() {
  local status=$?
  printf 'gerbil-bazel install_dependencies failed: phase=%s status=%s workspace=%s GERBIL_PATH=%s\n' \
    "$phase" "$status" "$workspace" "$gerbil_root" >&2
  exit "$status"
}
trap report_failure ERR

export GERBIL_PATH="$gerbil_root"
cd "$workspace"
mkdir -p "${gerbil_root%/}/pkg"

package_name_from_manifest() {
  local manifest=${1:?manifest path is required}
  tr '()\n\r\t' ' ' <"$manifest" |
    awk '{
      for (i = 1; i <= NF; i++) {
        if ($i == "package:" && i < NF) {
          print $(i + 1)
          exit
        }
      }
    }'
}

project_dependencies_ready() {
  local manifest="$workspace/gerbil.pkg"
  local dependency repository package package_manifest
  local dependencies=()

  test -f "$manifest" || return 1
  while IFS= read -r dependency; do
    dependencies+=("$dependency")
  done < <(
    tr '()\n\r\t' ' ' <"$manifest" |
      awk '{
        inside = 0
        for (i = 1; i <= NF; i++) {
          if ($i == "depend:") {
            inside = 1
          } else if ($i == "policy:") {
            exit
          } else if (inside && $i ~ /^"/) {
            gsub(/^"/, "", $i)
            gsub(/"$/, "", $i)
            print $i
          }
        }
      }'
  )

  test "${#dependencies[@]}" -gt 0 || return 1
  for dependency in "${dependencies[@]}"; do
    repository=${dependency%@*}
    package=$repository
    package_manifest="${gerbil_root%/}/pkg/$repository/gerbil.pkg"
    if [[ -f "$package_manifest" ]]; then
      package=$(package_name_from_manifest "$package_manifest")
      test -n "$package" || package=$repository
    fi
    test -e "${gerbil_root%/}/lib/$package" || return 1
  done
}

phase=install
timeout_seconds=${GERBIL_BAZEL_INSTALL_TIMEOUT_SECONDS:-600}
guard_receipt="${gerbil_root%/}/pkg/install-resource-guard.receipt.json"
install_command='
set -euo pipefail

is_positive_integer() {
  local value=${1:-}
  [[ ${#value} -le 18 && "$value" =~ ^[1-9][0-9]*$ ]]
}

explicit_cores=${GERBIL_BAZEL_INSTALL_BUILD_CORES:-}
cpu_count=${GERBIL_BAZEL_CPU_COUNT:-1}
configured_cores=${GERBIL_BUILD_CORES:-$cpu_count}
memory_bytes=${GERBIL_BAZEL_MEMORY_BYTES:-0}
memory_per_core_bytes=${GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES:-2147483648}

if ! is_positive_integer "$cpu_count"; then
  printf "GERBIL_BAZEL_CPU_COUNT must be a positive integer, got %s\n" \
    "$cpu_count" >&2
  exit 2
fi
if ! is_positive_integer "$configured_cores"; then
  printf "GERBIL_BUILD_CORES must be a positive integer, got %s\n" \
    "$configured_cores" >&2
  exit 2
fi
if [[ "$memory_bytes" != 0 ]] && ! is_positive_integer "$memory_bytes"; then
  printf "GERBIL_BAZEL_MEMORY_BYTES must be zero or a positive integer, got %s\n" \
    "$memory_bytes" >&2
  exit 2
fi
if ! is_positive_integer "$memory_per_core_bytes"; then
  printf "GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES must be a positive integer, got %s\n" \
    "$memory_per_core_bytes" >&2
  exit 2
fi

if [[ -n "$explicit_cores" ]]; then
  if ! is_positive_integer "$explicit_cores"; then
    printf "GERBIL_BAZEL_INSTALL_BUILD_CORES must be a positive integer, got %s\n" \
      "$explicit_cores" >&2
    exit 2
  fi
  install_cores=$explicit_cores
  decision=explicit
else
  install_cores=$configured_cores
  decision=adaptive-configured
fi

if (( memory_bytes > 0 )); then
  memory_core_limit=$((memory_bytes / memory_per_core_bytes))
  if (( memory_core_limit < 1 )); then
    memory_core_limit=1
  fi
  if (( install_cores > memory_core_limit )); then
    install_cores=$memory_core_limit
    if [[ "$decision" == explicit ]]; then
      decision=explicit-memory-cap
    else
      decision=adaptive-memory-cap
    fi
  fi
fi

printf "gerbil-bazel install_dependencies resources: decision=%s cores=%s configuredCores=%s cpu=%s memoryBytes=%s memoryPerCoreBytes=%s\n" \
  "$decision" "$install_cores" "$configured_cores" "$cpu_count" \
  "$memory_bytes" "$memory_per_core_bytes" >&2
exec /usr/bin/env "GERBIL_BUILD_CORES=$install_cores" "$@"
'
rm -f "$guard_receipt"
/usr/bin/env "${native_environment[@]}" \
  bash -c "$install_command" gerbil-bazel-install \
  "$gxi" "$resource_guard" "$guard_receipt" install-dependencies \
  "$timeout_seconds" "$gxpkg" deps --install &
install_pid=$!
if wait "$install_pid"; then
  install_status=0
else
  install_status=$?
fi

guard_receipt_proves_timeout() {
  [[ -f "$guard_receipt" ]] &&
    grep -Fq '"schema":"gerbil-bazel.resource-guard-receipt.v1"' "$guard_receipt" &&
    grep -Fq '"outcome":"timeout"' "$guard_receipt" &&
    grep -Eq '"exitCode":71([,}])' "$guard_receipt"
}

if (( install_status == 71 )) && guard_receipt_proves_timeout; then
  if project_dependencies_ready; then
    printf 'gerbil-bazel install_dependencies reached the %ss Scheme guard deadline after project dependencies became ready; receipt=%s\n' \
      "$timeout_seconds" "$guard_receipt" >&2
    exit 0
  fi
  printf 'gerbil-bazel install_dependencies reached the %ss Scheme guard deadline before project dependencies were ready; receipt=%s\n' \
    "$timeout_seconds" "$guard_receipt" >&2
  exit 124
fi
if (( install_status != 0 )); then
  printf 'gerbil-bazel install_dependencies Scheme guard failed: status=%s receipt=%s\n' \
    "$install_status" "$guard_receipt" >&2
  exit "$install_status"
fi
