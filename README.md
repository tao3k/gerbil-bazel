# gerbil-bazel

`gerbil-bazel` is a Bazel library for Gerbil toolchain capabilities and
content-addressed Gerbil package graphs.

The public package input is `gerbil.pkg`. A Gerbil-native evaluator reads the
manifest, computes a canonical source closure, and emits deterministic JSON.
Bazel validates that JSON, resolves explicitly pinned dependencies, generates a
static package graph, and executes the upstream `gxpkg build` lifecycle inside a
sandbox.

`build.ss` remains an opaque upstream Gerbil program. It is part of the hashed
source closure and is executed only through `gxpkg`; it is not a Bazel
attribute, a second build DSL, or a manifest field.

## Architecture

1. `gerbil.auto`, `gerbil.host`, or `gerbil.prebuilt` provides an immutable
   Gerbil toolchain capability.
2. `gerbil.package` selects the root `gerbil.pkg`.
3. `gerbil.dependency` binds every manifest dependency reference to an immutable
   archive, revision, and SHA-256 digest.
4. The repository phase evaluates every reachable manifest and rejects missing
   locks, extra locks, identity mismatches, duplicate packages, and cycles.
5. The generated repository exposes static package targets, source closures,
   graph evidence, and package build receipts.

The package graph never depends on mutable ambient package-manager state.

## Bzlmod API

```starlark
bazel_dep(name = "gerbil_bazel", version = "0.1.0")

gerbil = use_extension(
    "@gerbil_bazel//gerbil:extensions.bzl",
    "gerbil",
)

gerbil.auto(
    name = "local_gerbil",
    expected_version_prefixes = ["Gerbil v0.18.2"],
    linux_prebuilt_arch = "x86_64",
    linux_prebuilt_install_digest = "<installation digest>",
    linux_prebuilt_sha256 = "<archive sha256>",
    linux_prebuilt_urls = ["<immutable archive URL>"],
)

gerbil.package(
    manifest = "//:gerbil.pkg",
    name = "root_package",
)

gerbil.dependency(
    graph = "root_package",
    package = "<resolved package identity>",
    reference = "<manifest dependency reference>",
    revision = "<pinned revision>",
    sha256 = "<archive sha256>",
    strip_prefix = "<archive root>",
    urls = ["<immutable archive URL>"],
)

use_repo(gerbil, "local_gerbil", "root_package")

register_toolchains("@local_gerbil//:registered_toolchain")
```

The dependency `reference` is the name used by the parent manifest. `package`
is the identity declared by the downloaded dependency's own `gerbil.pkg`. Both
are validated.

## Generated targets

For a graph repository named `root_package`:

```text
@root_package//:build
@root_package//:build_receipt
@root_package//:gxpkg_manifest
@root_package//:package-graph.json
@root_package//:source_closure
@root_package//:package_0
```

Additional `package_N` targets are generated for the reachable dependency
closure. Generated target edges are static and follow the evaluated manifest
graph.

## Package consumer API

`@root_package//:build` carries the public `GerbilPackageInfo` capability.
Consumers use that capability rather than reconstructing package directories,
load paths, dependency roots, or toolchain environment:

```starlark
load(
    "@gerbil_bazel//gerbil:defs.bzl",
    "GerbilPackageInfo",
    "gerbil_test",
)

gerbil_test(
    name = "test",
    package = "@root_package//:build",
    tests = glob(["test/**/*-test.ss"]),
    environment = {
        "APPLICATION_MODE": "test",
    },
)
```

`gerbil_test` resolves the package root, its transitive package roots, and the
registered Gerbil libraries into one runtime load path. Test files follow the
upstream `gxtest` convention: export a phase-0 suite whose symbol ends in
`-test`.

The generated launcher performs setup and then terminally `exec`s `gxtest`.
There is no resident `native_scheme_env` or process-waiting wrapper. Child
success, failure, cancellation, and timeout status therefore reach Bazel
without a second process owner.

## Evidence

The evaluator emits `gerbil-bazel.package-manifest.v1`. The generated repository
emits `gerbil-bazel.package-graph.v1`, and each build emits
`gerbil-bazel.package-receipt.v1`.

The package receipt is a deterministic action artifact containing package
identity, locked revision, declared library-output requirement, and successful
status. Host-dependent duration, adaptive CPU and memory budget, and optional
process-guard observations are emitted separately as one structured
`gerbil-bazel.package-execution-telemetry.v1` stderr line. Telemetry remains
observable on cold execution but never enters the canonical cached receipt.

Graph evidence contains source and closure digests, dependency edges, evaluator
and Gerbil versions, and native ABI identity. Package action logs retain
upstream build output and execution telemetry.

Structural cache evidence is split into two stable documents.
`gerbil-bazel.build-scenario-receipt.v1` proves cold, identical, ambient
environment, and configuration frontiers.
`gerbil-bazel.cache-restoration-receipt.v1` links that receipt by SHA-256 and
proves root-source invalidation, dependency reverse-closure invalidation, and
explicit private-cache restoration in a second fresh Bazel output root.

Each package action also emits one upstream-compatible plain Scheme dependency
manifest. A parent action maps only its direct dependency manifests into its
private `GERBIL_PATH` before `gxpkg build`; the manifests already contain the
flattened transitive version closure produced by upstream. No package install,
link, Git discovery, or network operation runs inside a build action.

## Development

The declarative entry points are maintained in `justfile`:

```sh
just query
just build
just test
just scenario-test
just check
just lock-check
```

`just build` executes both the single-package and dependency-closure fixtures.
`just test` runs the Gerbil library and smoke-test suites.

The normative design is
[`docs/rfc/0006-gerbil-package-graph.org`](docs/rfc/0006-gerbil-package-graph.org).
