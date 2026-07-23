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
  printf 'fake static input\n' >"$payload/prefix/lib/fake.scm"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'compiler=' \
    'cc_options=' \
    'link_options=' \
    'mode=dynamic' \
    'probe=0' \
    'while (( $# > 0 )); do' \
    '  case "$1" in' \
    '    -cc) compiler="$2"; shift 2 ;;' \
    '    -cc-options) cc_options="$2"; shift 2 ;;' \
    '    -ld-options) link_options="$2"; shift 2 ;;' \
    '    -c | -link | -obj | -exe | -dynamic) mode="${1#-}"; shift ;;' \
    '    --synthetic-driver-probe) probe=1; shift ;;' \
    '    *) shift ;;' \
    '  esac' \
    'done' \
    '[[ "$probe" == 1 ]] || exit 1' \
    'printf "mode=%s\\ncompiler=%s\\nccOptions=%s\\nlinkOptions=%s\\n" "$mode" "$compiler" "$cc_options" "$link_options"' \
    >"$payload/prefix/bin/gsc"
  chmod +x "$payload/prefix/bin/gsc"
  set +e
  "$payload/prefix/bin/gsc" -link "$payload/prefix/lib/fake.scm" \
    >/dev/null 2>&1
  raw_gsc_failure_status=$?
  set -e
  if [[ "$raw_gsc_failure_status" != 1 ]]; then
    printf 'synthetic raw gsc failure contract expected 1, got %s\n' \
      "$raw_gsc_failure_status" >&2
    exit 1
  fi
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'C_COMPILER=/producer-only/ccache' \
    'FLAGS_OBJ=-fPIC' \
    'FLAGS_DYN=-bundle' \
    'if [[ "${1:-}" == C_COMPILER ]]; then printf "%s\\n" "$C_COMPILER"; fi' \
    'if [[ "${1:-}" == FLAGS_OBJ ]]; then printf "%s\\n" "$FLAGS_OBJ"; fi' \
    'if [[ "${1:-}" == FLAGS_DYN ]]; then printf "%s\\n" "$FLAGS_DYN"; fi' \
    'exit 0' >"$payload/prefix/bin/gambuild-C"
  chmod +x "$payload/prefix/bin/gambuild-C"

  for tool in gxc gxi gxpkg gxtest; do
    if [[ "$tool" == gxi ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        'if [[ "${1:-}" == --version ]]; then' \
        '  printf "Gerbil v0.prebuilt-test\\n"' \
        '  exit 0' \
        'fi' \
        'if [[ "${1##*/}" == resource_guard.ss ]]; then' \
        '  [[ $# -eq 7 ]]' \
        '  receipt=$2' \
        '  label=$3' \
        '  timeout_seconds=$4' \
        '  shift 4' \
        '  [[ -n "$receipt" ]]' \
        '  [[ "$label" == install-dependencies ]]' \
        '  [[ "$timeout_seconds" =~ ^[0-9]+$ ]]' \
        '  [[ $# -eq 3 ]]' \
        '  [[ "${1##*/}" == gxpkg ]]' \
        '  [[ "$2" == deps ]]' \
        '  [[ "$3" == --install ]]' \
        '  set +e' \
        '  "$@"' \
        '  child_status=$?' \
        '  set -e' \
        '  printf '\''{"childExitCode":%d,"exitCode":%d,"kind":"gerbil-bazel.resource-guard-receipt.v1","label":"install-dependencies","outcome":"completed","schema":"gerbil-bazel.resource-guard-receipt.v1","timeoutMs":%d,"version":1}\n'\'' \' \
        '    "$child_status" "$child_status" "$((timeout_seconds * 1000))" >"$receipt"' \
        '  exit "$child_status"' \
        'fi' \
        'printf '\''unexpected synthetic gxi command: %s\\n'\'' "$*" >&2' \
        'exit 64' >"$payload/prefix/bin/$tool"
    elif [[ "$tool" == gxc ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        'if [[ "${GERBIL_PROVIDER_GXC_FAILURE_STATUS:-0}" != 0 ]]; then' \
        '  exit "$GERBIL_PROVIDER_GXC_FAILURE_STATUS"' \
        'fi' \
        ': "${GAMBOPT:?GAMBOPT is required before gxc startup}"' \
        ': "${GERBIL_GCC:?GERBIL_GCC is required before gxc startup}"' \
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
        '[[ "$("$gambit_bin/gambuild-C" FLAGS_OBJ)" == -fPIC ]]' \
        '[[ "$("$gambit_bin/gambuild-C" FLAGS_DYN)" == -bundle ]]' \
        '[[ -x "$GERBIL_GSC" ]]' \
        '[[ -x "$GERBIL_GCC" ]]' \
        'case "$(uname -s)" in' \
        '  Darwin) expected_dynamic_link_options="-bundle -Wl,-undefined,dynamic_lookup" ;;' \
        '  Linux) expected_dynamic_link_options=-bundle ;;' \
        '  *) exit 64 ;;' \
        'esac' \
        'expected_dynamic_probe=$(printf "mode=dynamic\\ncompiler=%s\\nccOptions=\\nlinkOptions=%s" "$CC" "$expected_dynamic_link_options")' \
        '[[ "$("$GERBIL_GSC" --synthetic-driver-probe)" == "$expected_dynamic_probe" ]]' \
        '[[ "$("$GERBIL_GSC" -dynamic --synthetic-driver-probe)" == "$expected_dynamic_probe" ]]' \
        'expected_object_probe=$(printf "mode=obj\\ncompiler=%s\\nccOptions=-fPIC\\nlinkOptions=" "$CC")' \
        '[[ "$("$GERBIL_GSC" -obj --synthetic-driver-probe)" == "$expected_object_probe" ]]' \
        'for pass_through_mode in c link exe; do' \
        '  expected_pass_through_probe=$(printf "mode=%s\\ncompiler=\\nccOptions=\\nlinkOptions=" "$pass_through_mode")' \
        '  [[ "$("$GERBIL_GSC" "-$pass_through_mode" --synthetic-driver-probe)" == "$expected_pass_through_probe" ]]' \
        'done' \
        'link_failure_log=$(mktemp)' \
        'if "$GERBIL_GSC" -link "$GERBIL_HOME/lib/fake.scm" 2>"$link_failure_log"; then exit 65; fi' \
        'grep -Fq '\''GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT {"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"link","status":1'\'' "$link_failure_log"' \
        'grep -Fq '\''GERBIL_BAZEL_COMPILER_INPUT_RECEIPT {"kind":"gerbil-bazel.compiler-input-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"link","index":0'\'' "$link_failure_log"' \
        'grep -Fq '\''"sizeBytes":18,"digestAlgorithm":"sha256","digest":"'\'' "$link_failure_log"' \
        'rm -f "$link_failure_log"' \
        'for observed_failure_mode in obj dynamic; do' \
        '  mode_failure_log=$(mktemp)' \
        '  if "$GERBIL_GSC" "-$observed_failure_mode" "$GERBIL_HOME/lib/fake.scm" 2>"$mode_failure_log"; then exit 67; fi' \
        '  grep -Fq "\"driver\":\"GERBIL_GSC\",\"mode\":\"$observed_failure_mode\"" "$mode_failure_log"' \
        '  rm -f "$mode_failure_log"' \
        'done' \
        'link_failure_dir=$(mktemp -d)' \
        'if GERBIL_BAZEL_FAILURE_RECEIPT_DIR="$link_failure_dir" "$GERBIL_GSC" -link "$GERBIL_HOME/lib/fake.scm"; then exit 66; fi' \
        'link_failure_receipts=("$link_failure_dir"/*.jsonl)' \
        '[[ -f "${link_failure_receipts[0]}" ]]' \
        'while IFS= read -r receipt_json; do jq -e . <<<"$receipt_json" >/dev/null; done <"${link_failure_receipts[0]}"' \
        'grep -Fq '\''"kind":"gerbil-bazel.compiler-failure-receipt.v1"'\'' "${link_failure_receipts[0]}"' \
        'grep -Fq '\''"kind":"gerbil-bazel.compiler-input-receipt.v1"'\'' "${link_failure_receipts[0]}"' \
        'rm -rf "$link_failure_dir"' \
        'gcc_failure_log=$(mktemp)' \
        'if "$GERBIL_GCC" "$GERBIL_HOME/lib/does-not-exist.o" -o "$GERBIL_HOME/lib/does-not-exist" 2>"$gcc_failure_log"; then exit 68; fi' \
        'grep -Fq '\''"driver":"GERBIL_GCC","mode":"final-link"'\'' "$gcc_failure_log"' \
        'rm -f "$gcc_failure_log"' \
        'exit 0' >"$payload/prefix/bin/$tool"
    elif [[ "$tool" == gxpkg ]]; then
      printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        ': "${GERBIL_HOME:?GERBIL_HOME is required before gxpkg startup}"' \
        'if [[ "${1:-}" == deps && "${2:-}" == --install ]]; then' \
        '  : "${GERBIL_PATH:?GERBIL_PATH is required}"' \
        '  [[ "${GERBIL_BUILD_CORES:-}" =~ ^[1-9][0-9]*$ ]]' \
        '  resolved_gxi=$(command -v gxi)' \
        '  [[ "$(gxi --version)" == "Gerbil v0.prebuilt-test" ]]' \
        '  [[ "$resolved_gxi" == "$GERBIL_HOME/bin/gxi" ]]' \
        '  mkdir -p "$GERBIL_PATH/lib/clan" "$GERBIL_PATH/lib/gslph"' \
        '  printf "clan ready\\n" >"$GERBIL_PATH/lib/clan/ready.txt"' \
        '  printf "gslph ready\\n" >"$GERBIL_PATH/lib/gslph/ready.txt"' \
        '  printf "command=deps --install\\nGERBIL_PATH=%s\\nGERBIL_BUILD_CORES=%s\\n" "$GERBIL_PATH" "$GERBIL_BUILD_CORES" >"$GERBIL_PATH/install-dependencies.receipt"' \
        '  exit 0' \
        'fi' \
        'printf "unexpected synthetic gxpkg command: %s\\n" "$*" >&2' \
        'exit 64' >"$payload/prefix/bin/$tool"
    else
      printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$payload/prefix/bin/$tool"
    fi
    chmod +x "$payload/prefix/bin/$tool"
  done

  synthetic_install_digest="$(printf '1%.0s' {1..64})"
  jq -n \
    --arg system "$system" \
    --arg architecture "$architecture" \
    --arg install_digest "$synthetic_install_digest" \
    '{
      schema: "gerbil-bazel.prebuilt-capability-manifest.v1",
      capabilityId: "synthetic-prebuilt-test",
      installDigest: $install_digest,
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
manifest_install_digest="$(jq -er '.installDigest' "$manifest")"
expected_install_digest="${GERBIL_PREBUILT_INSTALL_DIGEST_OVERRIDE:-$manifest_install_digest}"
expect_install_digest_mismatch="${GERBIL_EXPECT_INSTALL_DIGEST_MISMATCH:-0}"
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
  -e "s|@@INSTALL_DIGEST@@|$expected_install_digest|g" \
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
  if [[ "$expect_install_digest_mismatch" == 1 ]]; then
    mismatch_log="$test_root/install-digest-mismatch.log"
    set +e
    "$bazel_bin" --output_user_root="$test_root/bazel" query \
      "@$repository_name//:registered_toolchain" \
      >"$mismatch_log" 2>&1
    mismatch_status=$?
    set -e
    if [[ "$mismatch_status" == 0 ]]; then
      printf 'prebuilt provider accepted a mismatched install digest\n' >&2
      exit 1
    fi
    grep -F 'Gerbil capability install digest mismatch' "$mismatch_log" >/dev/null
    jq -cn \
      --arg schema gerbil-bazel.repository-provider-test-receipt.v1 \
      --arg provider "$provider" \
      --arg manifest_install_digest "$manifest_install_digest" \
      --arg expected_install_digest "$expected_install_digest" \
      '{
        schema: $schema,
        outcome: "passed",
        provider: $provider,
        scenario: "install-digest-mismatch",
        manifestInstallDigest: $manifest_install_digest,
        expectedInstallDigest: $expected_install_digest,
        failedClosed: true,
        sourceFallback: false
      }'
    exit 0
  fi
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
    --arg install_digest "$expected_install_digest" \
    --arg selected_provider "$selected_provider" \
    --arg source "$expected_build_cores_source" \
    '(.environment | has("GERBIL_BUILD_CORES") | not) and
     (.environment | has("GERBIL_BAZEL_CPU_COUNT") | not) and
     (.environment | has("GERBIL_BAZEL_MEMORY_BYTES") | not) and
     ($selected_provider != "prebuilt" or .installDigest == $install_digest) and
     .gerbilBuildCores == ($build_cores | tonumber) and
     .gerbilBuildCoresSource == $source and
     (.systemCpuCount | type == "number") and
     (.systemMemoryBytes | type == "number") and
     (.gambitProducerOptions.dynamic | type == "string") and
     (.gambitProducerOptions.object | type == "string")' \
    "$output_base/$receipt_relative" >/dev/null
  if [[ "$selected_provider" == prebuilt && "$fixture" == synthetic ]]; then
    jq -e \
      '.gambitProducerOptions == {dynamic: "-bundle", object: "-fPIC"}' \
      "$output_base/$receipt_relative" >/dev/null
  fi
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
  if [[ "$selected_provider" == prebuilt && "$fixture" == synthetic ]]; then
    gxc_failure_dir="$test_root/gxc-failure-receipts"
    mkdir -p "$gxc_failure_dir"
    set +e
    GERBIL_PROVIDER_GXC_FAILURE_STATUS=23 \
      GERBIL_BAZEL_FAILURE_RECEIPT_DIR="$gxc_failure_dir" \
      "$bazel_bin" --output_user_root="$test_root/bazel" run \
      "@$repository_name//:gxc" -- \
      -d "$compiler_probe_output" "$compiler_probe_source" >/dev/null 2>&1
    gxc_failure_status=$?
    set -e
    if [[ "$gxc_failure_status" != 23 ]]; then
      printf 'gxc wrapper did not preserve controlled status 23: got %s\n' \
        "$gxc_failure_status" >&2
      exit 1
    fi
    gxc_failure_receipts=("$gxc_failure_dir"/*.jsonl)
    if [[ ! -f "${gxc_failure_receipts[0]}" ]]; then
      printf 'gxc wrapper did not emit an action-local compiler receipt\n' >&2
      exit 1
    fi
    while IFS= read -r receipt_json; do
      jq -e . <<<"$receipt_json" >/dev/null
    done <"${gxc_failure_receipts[0]}"
    grep -Fq '"kind":"gerbil-bazel.compiler-failure-receipt.v1"' \
      "${gxc_failure_receipts[0]}"
    grep -Fq '"driver":"GXC","mode":"compile-driver","status":23' \
      "${gxc_failure_receipts[0]}"
    grep -Fq '"kind":"gerbil-bazel.compiler-input-receipt.v1"' \
      "${gxc_failure_receipts[0]}"
    grep -Fq '"driver":"GXC","mode":"compile-driver","index":2' \
      "${gxc_failure_receipts[0]}"
  fi
  install_seconds=0
  dependency_transition=false
if [[ "$selected_provider" == prebuilt && "$fixture" == synthetic ]]; then
  install_launcher_relative="$(
    "$bazel_bin" --output_user_root="$test_root/bazel" cquery \
      "@$repository_name//:install_gerbil_dependencies.sh" \
      --output=files --noshow_progress 2>/dev/null
  )"
  install_launcher="$output_base/$install_launcher_relative"
  if grep -Eq '\{\{[A-Z_][A-Z0-9_]*\}\}' "$install_launcher"; then
    printf 'generated dependency installer contains unresolved template placeholders: %s\n' \
      "$install_launcher" >&2
    exit 1
  fi
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
  grep -Eq '^GERBIL_BUILD_CORES=[1-9][0-9]*$' \
    "$install_receipt"
  guard_receipt="$test_root/consumer/.gerbil/pkg/install-resource-guard.receipt.json"
  if [[ ! -f "$guard_receipt" ]]; then
    printf 'synthetic dependency guard did not emit %s\n' "$guard_receipt" >&2
    exit 1
  fi
  jq -e '
    .schema == "gerbil-bazel.resource-guard-receipt.v1" and
    .label == "install-dependencies" and
    .exitCode == 0
  ' "$guard_receipt" >/dev/null
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
