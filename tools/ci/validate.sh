#!/usr/bin/env bash
set -euo pipefail

bazel_bin="${BAZEL:-bazelisk}"

receipt_path="${RECEIPT_PATH:-.ci/receipts/validation.json}"
phases='[]'
gerbil_version=unavailable

write_receipt() {
  local outcome="$1"
  local exit_code="$2"
  local receipt_dir
  receipt_dir="$(dirname "$receipt_path")"
  mkdir -p "$receipt_dir"
  jq -n \
    --arg schema gerbil-bazel.ci-validation-receipt.v1 \
    --arg outcome "$outcome" \
    --arg os "$(uname -s)" \
    --arg arch "$(uname -m)" \
    --arg gerbil_version "$gerbil_version" \
    --arg bazel_version "$("$bazel_bin" --version)" \
    --argjson exit_code "$exit_code" \
    --argjson phases "$phases" \
    '{
      schema: $schema,
      outcome: $outcome,
      os: $os,
      arch: $arch,
      gerbil_version: $gerbil_version,
      bazel_version: $bazel_version,
      exit_code: $exit_code,
      phases: $phases
    }' >"$receipt_path"
}

run_phase() {
  local name="$1"
  shift
  local started_at="$SECONDS"
  local exit_code
  set +e
  "$@"
  exit_code="$?"
  set -e
  phases="$(
    jq -cn \
      --argjson phases "$phases" \
      --arg name "$name" \
      --argjson exit_code "$exit_code" \
      --argjson elapsed_seconds "$((SECONDS - started_at))" \
      '$phases + [{name: $name, exit_code: $exit_code, elapsed_seconds: $elapsed_seconds}]'
  )"
  if [[ "$exit_code" -ne 0 ]]; then
    write_receipt failed "$exit_code"
    return "$exit_code"
  fi
}

verify_gerbil_toolchain() {
  local version_path=.ci/gerbil-version.txt
  mkdir -p "$(dirname "$version_path")"
  "$bazel_bin" run @local_gerbil//:gxi -- --version \
    | tee "$version_path"
  grep -E 'Gerbil (v0\.18\.2|07c8481)' "$version_path" >/dev/null
}

run_phase gerbil-toolchain verify_gerbil_toolchain
gerbil_version="$(
  grep -E 'Gerbil (v0\.18\.2|07c8481)' .ci/gerbil-version.txt | head -n 1
)"
run_phase query "$bazel_bin" query //...
run_phase build "$bazel_bin" build //tests/smoke:compile
run_phase test "$bazel_bin" test \
  //tests/smoke:guarded_project_receipt_test \
  //tests/smoke:gxpkg_native_package_test \
  //tests/smoke:install_dependencies_test \
  //tests/smoke:project_library_view_test \
  //tests/smoke:project_receipt_test \
  //tests/smoke:test \
  //tests/smoke:toolchain_environment_test \
  --test_output=errors
run_phase atomic-package-cache env \
  BAZEL="$bazel_bin" \
  ATOMIC_RECEIPT_PATH="$(dirname "$receipt_path")/atomic-package-cache.json" \
  tools/ci/test_atomic_package_cache.sh
run_phase dev "$bazel_bin" run //tests/smoke:dev
write_receipt passed 0
jq -c . "$receipt_path"
