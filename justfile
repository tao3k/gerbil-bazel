set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := env_var_or_default("BAZEL", "bazelisk")
scenario_receipt := env_var_or_default("SCENARIO_RECEIPT", ".ci/receipts/build-scenarios.json")

default: check

query:
    {{ bazel }} query //...

build:
    {{ bazel }} build \
      @root_package//:build \
      @root_package_with_dependency//:build

test:
    {{ bazel }} test \
      //gerbil/... \
      //tests/smoke/... \
      --test_output=errors

scenario-test:
    tools/bench/run_build_scenarios.py \
      --bazel {{ bazel }} \
      --receipt {{ scenario_receipt }}

scenario-runner-test:
    python3 tools/bench/run_build_scenarios_test.py

source-identity-test:
    tools/ci/test_source_build_identity.sh
    tools/ci/test_source_build_checkpoint.sh
    tools/ci/test_bootstrap_gerbil.sh
    tools/ci/test_gerbil_bootstrap_attempt.sh
    tools/ci/test_install_materialization.sh
    tools/ci/test_source_producer_admission.sh
    tools/ci/test_source_producer_workflow.sh

promotion-authorization-test:
    tools/ci/test_authorize_prebuilt_promotion.sh

check: query build test scenario-runner-test source-identity-test promotion-authorization-test auto-test prebuilt-test

lock-check:
    {{ bazel }} mod deps --lockfile_mode=error

lock-update:
    {{ bazel }} mod deps --config=lock_update

mod-tidy:
    {{ bazel }} mod tidy --config=lock_update

prebuilt-test:
    tools/ci/test_repository_provider_receipt.sh \
      prebuilt \
      .ci/receipts/repository-provider-prebuilt.json
    GERBIL_EXPECT_INSTALL_DIGEST_MISMATCH=1 \
      GERBIL_PREBUILT_INSTALL_DIGEST_OVERRIDE=$(printf '0%.0s' {1..64}) \
      tools/ci/test_repository_provider_receipt.sh \
        prebuilt \
        .ci/receipts/repository-provider-prebuilt-install-digest-mismatch.json

auto-test:
    tools/ci/test_repository_provider_receipt.sh \
      auto \
      .ci/receipts/repository-provider-auto.json
