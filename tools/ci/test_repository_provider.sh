#!/usr/bin/env bash
set -euo pipefail

bazel_bin="${BAZEL:-bazelisk}"

provider="${1:-prebuilt}"
case "$provider" in
  auto | prebuilt) ;;
  *)
    printf 'usage: %s [auto|prebuilt]\n' "$0" >&2
    exit 64
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(cd "$(mktemp -d)" && pwd -P)"
cleanup() {
  if [[ "${GERBIL_PROVIDER_TEST_KEEP_ROOT:-0}" == 1 ]]; then
    printf 'preserved repository-provider test root: %s\n' "$test_root" >&2
  else
    rm -rf "$test_root"
  fi
}
trap cleanup EXIT

normalize_system() {
  case "$1" in
    Darwin) printf 'darwin\n' ;;
    Linux) printf 'linux\n' ;;
    *) return 64 ;;
  esac
}

normalize_arch() {
  case "$1" in
    amd64 | x86_64) printf 'x86_64\n' ;;
    aarch64 | arm64) printf 'aarch64\n' ;;
    *) return 64 ;;
  esac
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

system="$(normalize_system "$(uname -s)")"
architecture="$(normalize_arch "$(uname -m)")"
case "$system" in
  darwin) logical_cpu_count="$(/usr/sbin/sysctl -n hw.logicalcpu)" ;;
  linux) logical_cpu_count="$(getconf _NPROCESSORS_ONLN)" ;;
esac
expected_build_cores="${GERBIL_BUILD_CORES:-$logical_cpu_count}"
expected_build_cores_source=host-system
if [[ -n "${GERBIL_BUILD_CORES:-}" ]]; then
  expected_build_cores_source=process-environment
fi
mkdir -p "$test_root/consumer"
fixture=provided
archive="${GERBIL_PREBUILT_ARCHIVE:-}"
if [[ -z "$archive" ]]; then
  fixture=synthetic
  payload="$test_root/payload"
  mkdir -p "$payload/prefix/bin" "$payload/prefix/lib"
  printf 'fake dependency\n' >"$payload/prefix/lib/fake.ss"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'compiler=' \
    'link_options=' \
    'mode=' \
    'probe=0' \
    'while (( $# > 0 )); do' \
    '  case "$1" in' \
    '    -cc) compiler="$2"; shift 2 ;;' \
    '    -ld-options) link_options="$2"; shift 2 ;;' \
    '    -dynamic | -exe) mode="${1#-}"; shift ;;' \
    '    --synthetic-driver-probe) probe=1; shift ;;' \
    '    *) shift ;;' \
    '  esac' \
    'done' \
    '[[ "$probe" == 1 ]]' \
    'printf "mode=%s\\ncompiler=%s\\nlinkOptions=%s\\n" "$mode" "$compiler" "$link_options"' \
    >"$payload/prefix/bin/gsc"
  chmod +x "$payload/prefix/bin/gsc"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'C_COMPILER=/producer-only/ccache' \
    'FLAGS_DYN=-bundle' \
    'if [[ "${1:-}" == C_COMPILER ]]; then printf "%s\\n" "$C_COMPILER"; fi' \
    'if [[ "${1:-}" == FLAGS_DYN ]]; then printf "%s\\n" "$FLAGS_DYN"; fi' \
    'exit 0' >"$payload/prefix/bin/gambuild-C"
  chmod +x "$payload/prefix/bin/gambuild-C"

  for tool in gxc gxi gxpkg gxtest; do
    if [[ "$tool" == gxi ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'if [[ "${1:-}" == --version ]]; then printf "Gerbil v0.prebuilt-test\\n"; fi' \
        'exit 0' >"$payload/prefix/bin/$tool"
    elif [[ "$tool" == gxc ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        ': "${GAMBOPT:?GAMBOPT is required before gxc startup}"' \
        ': "${GERBIL_GSC:?GERBIL_GSC is required before gxc startup}"' \
        '[[ ",$GAMBOPT," == *,"~~=$GERBIL_HOME",* ]]' \
        '[[ ",$GAMBOPT," == *,"~~lib=$GERBIL_HOME/lib",* ]]' \
        'gambit_bin=' \
        'IFS="," read -r -a gambit_options <<<"$GAMBOPT"' \
        'for option in "${gambit_options[@]}"; do' \
        '  if [[ "$option" == "~~bin="* ]]; then gambit_bin="${option#~~bin=}"; fi' \
        'done' \
        ': "${gambit_bin:?GAMBOPT must map ~~bin}"' \
        '[[ "$("$gambit_bin/gambuild-C" C_COMPILER)" == /producer-only/ccache ]]' \
        '[[ "$("$gambit_bin/gambuild-C" FLAGS_DYN)" == -bundle ]]' \
        '[[ -x "$GERBIL_GSC" ]]' \
        'case "$(uname -s)" in' \
        '  Darwin) expected_dynamic_link_options=-Wl,-undefined,dynamic_lookup ;;' \
        '  Linux) expected_dynamic_link_options= ;;' \
        '  *) exit 64 ;;' \
        'esac' \
        'dynamic_probe=$("$GERBIL_GSC" -dynamic --synthetic-driver-probe)' \
        'expected_dynamic_probe=$(printf "mode=dynamic\\ncompiler=%s\\nlinkOptions=%s" "$CC" "$expected_dynamic_link_options")' \
        '[[ "$dynamic_probe" == "$expected_dynamic_probe" ]]' \
        'executable_probe=$("$GERBIL_GSC" -exe --synthetic-driver-probe)' \
        'expected_executable_probe=$(printf "mode=exe\\ncompiler=%s\\nlinkOptions=" "$GERBIL_GCC")' \
        '[[ "$executable_probe" == "$expected_executable_probe" ]]' \
        'exit 0' >"$payload/prefix/bin/$tool"
    elif [[ "$tool" == gxpkg ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        ': "${GERBIL_HOME:?GERBIL_HOME is required before gxpkg startup}"' \
        'if [[ "${1:-}" == deps && "${2:-}" == --install ]]; then' \
        '  : "${GERBIL_PATH:?GERBIL_PATH is required}"' \
        '  resolved_gxi=$(command -v gxi)' \
        '  [[ "$(gxi --version)" == "Gerbil v0.prebuilt-test" ]]' \
        '  [[ "$resolved_gxi" == "$GERBIL_HOME/bin/gxi" ]]' \
        '  mkdir -p "$GERBIL_PATH/lib/clan" "$GERBIL_PATH/lib/gslph"' \
        '  printf "clan ready\\n" >"$GERBIL_PATH/lib/clan/ready.txt"' \
        '  printf "gslph ready\\n" >"$GERBIL_PATH/lib/gslph/ready.txt"' \
        '  printf "command=deps --install\\nGERBIL_PATH=%s\\n" "$GERBIL_PATH" >"$GERBIL_PATH/install-dependencies.receipt"' \
        '  exit 0' \
        'fi' \
        'printf "unexpected synthetic gxpkg command: %s\\n" "$*" >&2' \
        'exit 64' >"$payload/prefix/bin/$tool"
    else
      printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$payload/prefix/bin/$tool"
    fi
    chmod +x "$payload/prefix/bin/$tool"
  done

  jq -n \
    --arg system "$system" \
    --arg architecture "$architecture" \
    '{
      schema: "gerbil-bazel.prebuilt-capability-manifest.v1",
      capabilityId: "synthetic-prebuilt-test",
      version: "Gerbil v0.prebuilt-test",
      nativeAbiFingerprint: "0000000000000000000000000000000000000000",
      platform: {os: $system, arch: $architecture},
      gerbilHome: "prefix",
      tools: {
        gxc: "prefix/bin/gxc",
        gxi: "prefix/bin/gxi",
        gxpkg: "prefix/bin/gxpkg",
        gxtest: "prefix/bin/gxtest"
      },
      dependencyRoots: ["prefix/lib"],
      environment: {}
    }' >"$payload/gerbil-bazel-capability.json"

  archive="$test_root/prebuilt.tar.gz"
  tar -C "$payload" -czf "$archive" .
  manifest="$payload/gerbil-bazel-capability.json"
else
  archive="$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")"
  if [[ ! -f "$archive" ]]; then
    printf 'provided Gerbil capability archive does not exist: %s\n' "$archive" >&2
    exit 66
  fi
  manifest="${archive%.tar.gz}.manifest.json"
  if [[ ! -f "$manifest" ]]; then
    manifest="$test_root/provided-manifest.json"
    tar -xOzf "$archive" ./gerbil-bazel-capability.json >"$manifest"
  fi
fi

archive_sha256="$(sha256_file "$archive")"
archive_url="file://$archive"
repository_name="${provider}_gerbil"
template="$repo_root/tests/$provider/MODULE.bazel.tpl"
expected_version="$(jq -er '.version' "$manifest")"
host_tool_paths='{"gxi": "/gerbil-auto-provider-must-not-use-host"}'
selected_provider=prebuilt
if [[ "$provider" == auto && "$system" == darwin ]]; then
  # A Darwin auto provider must never touch the Linux-only archive inputs.
  archive_sha256="$(printf '0%.0s' {1..64})"
  archive_url="file:///gerbil-auto-provider-must-not-fetch-linux-archive"
  expected_version="$(gxi --version)"
  host_tool_paths='{}'
  selected_provider=host
fi

sed \
  -e "s|@@GERBIL_BAZEL_PATH@@|$repo_root|g" \
  -e "s|@@ARCHITECTURE@@|$architecture|g" \
  -e "s|@@ARCHIVE_URL@@|$archive_url|g" \
  -e "s|@@ARCHIVE_SHA256@@|$archive_sha256|g" \
  -e "s|@@HOST_TOOL_PATHS@@|$host_tool_paths|g" \
  "$template" \
  >"$test_root/consumer/MODULE.bazel"
provider_fixture="$repo_root/tests/repository-provider"
sed \
  -e "s|@@REPOSITORY_NAME@@|$repository_name|g" \
  "$provider_fixture/consumer.BUILD.bazel.tpl" \
  >"$test_root/consumer/BUILD.bazel"
cp "$provider_fixture/project-root.marker" "$test_root/consumer/project-root.marker"
cp "$provider_fixture/project_library_view_test.sh" \
  "$test_root/consumer/project_library_view_test.sh"
cp "$provider_fixture/project_dependency_state_test.sh" \
  "$test_root/consumer/project_dependency_state_test.sh"
if [[ "$selected_provider" != prebuilt || "$fixture" != synthetic ]]; then
  mkdir -p "$test_root/consumer/.gerbil/lib"
  cp -R "$provider_fixture/project-library/." "$test_root/consumer/.gerbil/lib/"
fi
if [[ "$selected_provider" == prebuilt && "$fixture" == synthetic ]]; then
  ambient_bin="$test_root/ambient-bin"
  mkdir -p "$ambient_bin"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'printf "ambient gxi must not run\n" >&2' \
    'exit 97' \
    >"$ambient_bin/gxi"
  chmod +x "$ambient_bin/gxi"
  export PATH="$ambient_bin:$PATH"
fi

(
  cd "$test_root/consumer"
  provider_started_at="$SECONDS"
  "$bazel_bin" --output_user_root="$test_root/bazel" query \
    "@$repository_name//:registered_toolchain"
  provider_seconds="$((SECONDS - provider_started_at))"
  output_base="$(
    "$bazel_bin" --output_user_root="$test_root/bazel" info output_base \
      --noshow_progress 2>/dev/null
  )"
  receipt_relative="$(
    "$bazel_bin" --output_user_root="$test_root/bazel" cquery \
      "@$repository_name//:toolchain.receipt.json" \
      --output=files --noshow_progress 2>/dev/null
  )"
  jq -e \
    --arg build_cores "$expected_build_cores" \
    --arg source "$expected_build_cores_source" \
    '.environment.GERBIL_BUILD_CORES == $build_cores and
     .gerbilBuildCores == ($build_cores | tonumber) and
     .gerbilBuildCoresSource == $source' \
    "$output_base/$receipt_relative" >/dev/null
  tool_started_at="$SECONDS"
  observed_version="$(
    "$bazel_bin" --output_user_root="$test_root/bazel" run \
      "@$repository_name//:gxi" -- --version 2>/dev/null
  )"
  if [[ "$observed_version" != "$expected_version" ]]; then
    printf '%s repository runtime probe mismatch: expected %s, got %s\n' \
      "$provider" "$expected_version" "$observed_version" >&2
    exit 1
  fi
  tool_seconds="$((SECONDS - tool_started_at))"
  compiler_probe_source="$test_root/consumer/compiler-driver-probe.ss"
  compiler_probe_output="$test_root/consumer/compiler-driver-probe-lib"
  mkdir -p "$compiler_probe_output"
  printf '%s\n' \
    '(export compiler-driver-ready)' \
    "(def compiler-driver-ready 'ready)" \
    >"$compiler_probe_source"
  "$bazel_bin" --output_user_root="$test_root/bazel" run \
    "@$repository_name//:gxc" -- \
    -d "$compiler_probe_output" "$compiler_probe_source" >/dev/null
  compiler_driver_verified=true
  install_seconds=0
  dependency_transition=false
  if [[ "$selected_provider" == prebuilt && "$fixture" == synthetic ]]; then
    "$bazel_bin" --output_user_root="$test_root/bazel" build \
      //:project_dependency_state_missing_test
    install_started_at="$SECONDS"
    "$bazel_bin" --output_user_root="$test_root/bazel" run \
      "@$repository_name//:install_dependencies"
    install_seconds="$((SECONDS - install_started_at))"
    install_receipt="$test_root/consumer/.gerbil/install-dependencies.receipt"
    if [[ ! -f "$install_receipt" ]]; then
      printf 'synthetic dependency installer did not emit %s\n' \
        "$install_receipt" >&2
      find "$test_root/consumer/.gerbil" -maxdepth 3 -print >&2 || true
      exit 1
    fi
    grep -Fx 'command=deps --install' "$install_receipt" >/dev/null
    expected_gerbil_path="$(cd "$test_root/consumer/.gerbil" && pwd -P)"
    grep -Fx "GERBIL_PATH=$expected_gerbil_path" \
      "$install_receipt" >/dev/null
    dependency_transition=true
  fi
  project_view_started_at="$SECONDS"
  "$bazel_bin" --output_user_root="$test_root/bazel" build //:project_library_view_test
  project_view_seconds="$((SECONDS - project_view_started_at))"
  jq -cn \
    --arg schema gerbil-bazel.repository-provider-test-receipt.v1 \
    --arg provider "$provider" \
    --arg selected_provider "$selected_provider" \
    --arg fixture "$fixture" \
    --arg version "$observed_version" \
    --argjson compiler_driver_verified "$compiler_driver_verified" \
    --argjson dependency_transition "$dependency_transition" \
    --argjson install_seconds "$install_seconds" \
    --argjson provider_seconds "$provider_seconds" \
    --argjson project_view_seconds "$project_view_seconds" \
    --argjson tool_seconds "$tool_seconds" \
    '{
      schema: $schema,
      outcome: "passed",
      provider: $provider,
      selectedProvider: $selected_provider,
      fixture: $fixture,
      version: $version,
      compilerDriverVerified: $compiler_driver_verified,
      dependencyTransition: $dependency_transition,
      installSeconds: $install_seconds,
      providerSeconds: $provider_seconds,
      projectViewSeconds: $project_view_seconds,
      toolSeconds: $tool_seconds,
      totalSeconds: ($provider_seconds + $install_seconds + $project_view_seconds + $tool_seconds)
    }'
)
