# Gerbil Bazel

`gerbil-bazel` provides reusable Bazel APIs for discovering a native Gerbil
installation and building Gerbil projects on Darwin and Linux. It is independent
of any application framework: the consumer's `build.ss` remains the canonical
description of module topology and project semantics.

## Bzlmod setup

Use one platform-adaptive declaration when Darwin should resolve the native
Homebrew installation and Linux should import an immutable prebuilt capability:

```starlark
gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.auto(
    name = "local_gerbil",
    expected_version_prefixes = ["Gerbil 07c8481", "Gerbil v0.18.2"],
    linux_prebuilt_arch = "x86_64",
    linux_prebuilt_install_digest = "ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208",
    linux_prebuilt_sha256 = "741d67f1d1a37e057181bfe8b3348ce2a9cfce06ac3b9c4e914400978f9d5fe7",
    linux_prebuilt_urls = [
        "https://github.com/tao3k/gerbil-bazel/releases/download/gerbil-v0.18.2-07c84815-linux-x86_64-ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208/gerbil-v0.18.2-07c84815-linux-x86_64-ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208.tar.gz",
    ],
    project_dependency_packages = ["clan", "gslph"],
    project_root_marker = "//:MODULE.bazel",
)
use_repo(gerbil, "local_gerbil")
register_toolchains("@local_gerbil//:registered_toolchain")
```

The extension resolves `auto` before repository creation and instantiates
exactly one provider. Darwin uses native host discovery; Linux validates that
the declared archive architecture matches the runner and instantiates the
prebuilt provider. Unsupported systems and architecture mismatches fail closed.
The module extension is declared `os_dependent` and `arch_dependent`, so Bazel
records separate operating-system and architecture evaluations instead of
reusing a Darwin-generated provider graph on Linux or a Linux prebuilt graph
across incompatible architectures through `MODULE.bazel.lock`.

Use explicit native host discovery when the consumer does not need automatic
cross-platform selection:

```starlark
gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.host(name = "local_gerbil")
use_repo(gerbil, "local_gerbil")
register_toolchains("@local_gerbil//:registered_toolchain")
```

Use the explicit immutable provider for a Linux-only consumer:

```starlark
gerbil = use_extension("@gerbil_bazel//gerbil:extensions.bzl", "gerbil")
gerbil.prebuilt(
    install_digest = "ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208",
    name = "gerbil_linux_x86_64",
    expected_version_prefixes = ["Gerbil v0.18.2", "Gerbil 07c8481"],
    sha256 = "741d67f1d1a37e057181bfe8b3348ce2a9cfce06ac3b9c4e914400978f9d5fe7",
    urls = [
        "https://github.com/tao3k/gerbil-bazel/releases/download/gerbil-v0.18.2-07c84815-linux-x86_64-ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208/gerbil-v0.18.2-07c84815-linux-x86_64-ee5a236818e1b8fd9cc6e886b510795495e95402e790892961e6a1059a5c3208.tar.gz",
    ],
)
use_repo(gerbil, "gerbil_linux_x86_64")
register_toolchains("@gerbil_linux_x86_64//:registered_toolchain")
```

The prebuilt provider validates the archive digest, embedded manifest, execution
platform, runtime version, and native ABI shape. It fails closed and never
falls back to a source build. See
[RFC 0002](docs/rfc/0002-prebuilt-linux-capability.org) for the archive,
release, receipt, and performance contracts.

Source production is a separate, explicit operation.  The
[Source Producer v1 runbook](docs/runbooks/source-producer-v1.org) defines
default-branch registration, runner selection, cold-build receipt acceptance,
and the independent promotion boundary.

Both `auto` providers and the explicit `prebuilt` provider support the same
project-library view as `host`. Declare `project_root_marker`,
`project_library_relative_path`, and `project_dependency_packages`; the
repository projects ready packages into `lib/<package>` and records every
package as `ready` or `missing` in `toolchain.receipt.json`. This keeps the
downstream BUILD graph identical on Darwin and Linux while leaving dependency
installation under the separate `install_dependencies` capability.

Every host and prebuilt repository publishes `//:install_dependencies`. The
launcher enters the consumer workspace, uses its workspace-local `.gerbil`
root, and runs the standard `gxpkg deps --install` command through the selected
provider environment. Gerbil-Bazel does not wrap this command in another
`gxpkg env` lifecycle and does not duplicate package-manager verification with
an unconditional `gxpkg list`. A dependency installation can make
previously missing project packages ready; the next Bazel command then
re-evaluates the watched project-library view.

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
environment. This is an explicit developer-side effect target, never build
truth inside a hermetic compile action.

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
    args = ["compile", "--tests"],
    srcs = glob(["src/**/*.ss"]),
)

gerbil_project_dev(
    name = "scheme_dev",
    build_script = "build.ss",
    args = ["compile", "--tests"],
)

gerbil_project_test(
    name = "scheme_test",
    project = ":scheme",
    srcs = glob(["test/**/*.ss"]),
    tests = ["test/project-test.ss"],
)
```

The compile action stages every declared source in a writable tree before it
executes `build.ss`. Tests always consume an explicit `GerbilProjectInfo`, so a
matrix reuses one compile action. Set `receipt_line_prefix` when the build
script emits canonical JSON. Every action receipt keeps the stable outer
`gerbil-bazel.project-receipt.v1` schema and its original six required fields.
The validated producer value is nested under the optional `buildReceipt`
field. Guarded project actions also expose their Scheme resource-guard evidence
under the optional `resourceGuard` field. The normative contract is
`schemas/gerbil-bazel.project-receipt.v1.schema.json`; execution capability
changes do not create a new project receipt version.

Host-specific paths, available logical CPUs, physical memory, compiler,
assembler, linker, SDK, optional Homebrew native libraries, and Gerbil
executables are discovered dynamically. Override only explicit capabilities
such as `GERBIL_CC`, `GERBIL_GXI`, or `GERBIL_NATIVE_ABI`. For fully declared
installations, `gerbil.host(tool_paths = {...})` takes precedence over
environment overrides and `PATH` discovery.

Gerbil-Bazel leaves the installed `gambuild-C` immutable. Repository discovery
reads its literal `C_COMPILER` declaration and queries `FLAGS_DYN` and
`FLAGS_OBJ` without writing the installation. A generated executable-path
`GERBIL_GSC` launcher uses Gambit's public `-cc`, `-cc-options`, and
`-ld-options` interfaces. Because a `-cc` override clears Gambit's configured
mode flags, implicit or explicit dynamic compilation restores the complete
`FLAGS_DYN` value before adding any platform option, while `-obj` restores the
complete `FLAGS_OBJ` value. `-c`, `-link`, and `-exe` pass through without a
wrapper-added compiler override.

On Darwin, dynamic compilation appends `-Wl,-undefined,dynamic_lookup` after
the installed producer flags, and Gerbil's public `GERBIL_GCC` boundary selects
the Xcode Clang driver for the final executable link. Linux restores the same
installed producer mode flags without the Darwin option or a separate final
link driver. `gambitProducerOptions`, `gambitDynamicLinkOptions`, and
`gerbilExecutableLinker` are recorded in `toolchain.receipt.json` and
participate in Bazel action identity.

Package semantics remain upstream-owned. `gerbil.pkg` owns package and
dependency metadata, `gxpkg` owns package lifecycle, and `build.ss` plus
`std/make` own compile membership, ordering, and incrementality. Bazel declares
the source closure and dependency tree artifacts needed by the sandbox; it does
not expose a second package identity/revision graph.
