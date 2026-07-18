set shell := ["bash", "-euo", "pipefail", "-c"]

bazel := env_var_or_default("BAZEL", "bazel")

default: check

query:
    {{bazel}} query //...

build:
    {{bazel}} build //tests/smoke:compile

test:
    {{bazel}} test //tests/smoke:test --test_output=errors

dev:
    {{bazel}} run //tests/smoke:dev

check: query build test

mod-tidy:
    {{bazel}} mod tidy
