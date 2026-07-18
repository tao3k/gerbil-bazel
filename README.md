# Gerbil Bazel

`gerbil-bazel` provides reusable Bazel APIs for discovering a native Gerbil
installation and building Gerbil projects on Darwin and Linux. It is independent
of any application framework: the consumer's `build.ss` remains the canonical
description of module topology and project semantics.

## Bzlmod setup

Use native host discovery for local development:

```starlark
gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.host(name = "local_gerbil")
use_repo(gerbil, "local_gerbil")
register_toolchains("@local_gerbil//:registered_toolchain")
```

Use an immutable prebuilt capability when Linux CI must not compile Gerbil:

```starlark
gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.prebuilt(
    name = "gerbil_linux_x86_64",
    expected_version_prefixes = ["0.18.2"],
    sha256 = "<archive-sha256>",
    urls = ["<immutable-release-archive-url>"],
)
use_repo(gerbil, "gerbil_linux_x86_64")
register_toolchains("@gerbil_linux_x86_64//:registered_toolchain")
```

The prebuilt provider validates the archive digest, embedded manifest, execution
platform, runtime version, and native ABI shape. It fails closed and never
falls back to a source build. See
[RFC 0002](docs/rfc/0002-prebuilt-linux-capability.org) for the archive,
release, receipt, and performance contracts.

```starlark
bazel_dep(name = "gerbil_bazel", version = "0.1.0")
bazel_dep(name = "platforms", version = "1.0.0")
bazel_dep(name = "rules_shell", version = "0.8.0")

gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.host(
    name = "local_gerbil",
    expected_version_prefixes = ["0.18.2"],
)
use_repo(gerbil, "local_gerbil")
register_toolchains("@local_gerbil//:registered_toolchain")
```

During local development, add a `local_path_override` for `gerbil_bazel` in the
consumer module. Published consumers should use a registry release instead.

## Project dependency installation

Each discovered host repository publishes a workspace-aware dependency target:

```bash
bazel run @local_gerbil//:install_dependencies
```

The target enters `BUILD_WORKSPACE_DIRECTORY`, defaults `GERBIL_PATH` to
`$BUILD_WORKSPACE_DIRECTORY/.gerbil`, runs the standard
`gxpkg deps --install` workflow through the normalized native tool
environment, and finishes with `gxpkg list` as an executable verification.

## Project rules

```starlark
load(
    "@gerbil_bazel//gerbil:defs.bzl",
    "gerbil_project_compile",
    "gerbil_project_dev",
    "gerbil_project_test",
)

gerbil_project_compile(
    name = "scheme",
    build_script = "build.ss",
    srcs = glob(["src/**/*.ss"]),
    args = ["compile", "--tests"],
)

gerbil_project_dev(
    name = "scheme_dev",
    build_script = "build.ss",
    args = ["compile", "--tests"],
)

gerbil_project_test(
    name = "scheme_test",
    build_script = "build.ss",
    srcs = glob(["src/**/*.ss", "test/**/*.ss"]),
    build_args = ["compile", "--tests"],
    tests = ["test/project-test.ss"],
)
```

Host-specific paths, available logical CPUs, physical memory, compiler,
assembler, linker, SDK, optional Homebrew native libraries, and Gerbil
executables are discovered dynamically. Override only explicit capabilities
such as `GERBIL_CC`, `GERBIL_GXI`, or `GERBIL_NATIVE_ABI`. For fully declared
installations, `gerbil.host(tool_paths = {...})` takes precedence over
environment overrides and `PATH` discovery.
