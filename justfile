set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := env_var_or_default("BAZEL", "bazel")

default: check

query:
    {{bazel}} query //...

build:
    {{bazel}} build \
      //tests/smoke:compile \
      //tests/smoke:receipt_compile

test:
    {{bazel}} test \
      //gerbil:run_project_test \
      //tests/smoke:install_dependencies_test \
      //tests/smoke:project_receipt_test \
      //tests/smoke:project_library_view_test \
      //tests/smoke:reuse_test_one \
      //tests/smoke:reuse_test_two \
      //tests/smoke:test \
      //tests/smoke:toolchain_environment_test \
      --test_output=errors

dev:
    {{bazel}} run //tests/smoke:dev

check: query build test auto-test prebuilt-test

mod-tidy:
    {{bazel}} mod tidy

prebuilt-test:
    tools/ci/test_repository_provider.sh prebuilt

auto-test:
    tools/ci/test_repository_provider.sh auto
