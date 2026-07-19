set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := "bazelisk"

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

check: query build test auto-test prebuilt-test

mod-tidy:
    {{ bazel }} mod tidy

prebuilt-test:
    tools/ci/test_repository_provider.sh prebuilt

auto-test:
    tools/ci/test_repository_provider.sh auto
