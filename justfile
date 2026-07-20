set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := env_var_or_default("BAZEL", "bazelisk")
scenario_receipt := env_var_or_default("SCENARIO_RECEIPT", ".ci/receipts/build-scenarios.json")

default: check

query:
    {{ bazel }} query //...

build:
    {{ bazel }} build \
      //tests/smoke:compile \
      //tests/smoke:receipt_compile

test:
    {{ bazel }} test \
      //gerbil:run_project_test \
      //gerbil:project_receipt_schema_test \
      //gerbil:project_receipt_v1_instances_test \
      //gerbil:resource_guard_test \
      //gerbil:validate_json_test \
      //tests/smoke:guarded_project_receipt_test \
      //tests/smoke:gxpkg_native_package_test \
      //tests/smoke:install_dependencies_test \
      //tests/smoke:native_math_receipt_test \
      //tests/smoke:project_receipt_test \
      //tests/smoke:project_library_view_test \
      //tests/smoke:reuse_test_one \
      //tests/smoke:reuse_test_two \
      //tests/smoke:source_root_test \
      //tests/smoke:test \
      //tests/smoke:toolchain_environment_test \
      --test_output=errors

dev:
    {{ bazel }} run //tests/smoke:dev

dev-test:
    {{ bazel }} run //tests/smoke:dev_test

scenario-test:
    tools/bench/run_build_scenarios.py \
      --bazel {{ bazel }} \
      --receipt {{ scenario_receipt }}

source-identity-test:
    tools/ci/test_source_build_identity.sh
    tools/ci/test_bootstrap_gerbil.sh
    tools/ci/test_install_materialization.sh

promotion-authorization-test:
    tools/ci/test_authorize_prebuilt_promotion.sh

check: query build test source-identity-test promotion-authorization-test auto-test prebuilt-test

mod-tidy:
    {{ bazel }} mod tidy

prebuilt-test:
    tools/ci/test_repository_provider.sh prebuilt
    GERBIL_EXPECT_INSTALL_DIGEST_MISMATCH=1 \
      GERBIL_PREBUILT_INSTALL_DIGEST_OVERRIDE=$(printf '0%.0s' {1..64}) \
      tools/ci/test_repository_provider.sh prebuilt

auto-test:
    tools/ci/test_repository_provider.sh auto
