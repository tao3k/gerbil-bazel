set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := env_var_or_default("BAZEL", "bazel")

default: check

query:
    {{bazel}} query //...

build:
    {{bazel}} build //tests/smoke:compile

test:
    {{bazel}} test \
      //tests/smoke:project_library_view_test \
      //tests/smoke:test \
      //tests/smoke:toolchain_environment_test \
      --test_output=errors

dev:
    {{bazel}} run //tests/smoke:dev

check: query build test prebuilt-test

mod-tidy:
    {{bazel}} mod tidy

prebuilt-test:
    tools/ci/test_prebuilt_repository.sh
