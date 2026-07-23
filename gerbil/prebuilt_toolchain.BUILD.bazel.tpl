load("@gerbil_bazel//gerbil:toolchain.bzl", "gerbil_toolchain")
load("@gerbil_bazel//gerbil:script.bzl", "gerbil_scheme_executable")
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")

package(default_visibility = ["//visibility:public"])

sh_binary(name = "native_scheme_env", srcs = ["native_scheme_env.sh"])

gerbil_scheme_executable(
    name = "install_dependencies",
    compiler = ":gxc",
    gxpkg = "bin/gxpkg_raw",
    script = "install_gerbil_dependencies.ss",
    data = [
        "bin/gxpkg_raw",
        "native_abi.txt",
    ],
    includes = ["resource_policy.ss"],
)

{{TOOL_RULES}}

filegroup(
    name = "dependency_libraries",
    srcs = glob(["lib/**"], exclude = ["lib/.root"], allow_empty = True),
)

filegroup(
    name = "dependency_library_root",
    srcs = ["lib/.root"],
)

gerbil_toolchain(
    name = "toolchain_impl",
    dependency_libraries = ":dependency_libraries",
    dependency_library_root = "lib/.root",
    environment = {{ENVIRONMENT_DICT}},
    gerbil_as = {{GERBIL_AS}},
    gerbil_cc = {{GERBIL_CC}},
    gerbil_gcc = {{GERBIL_GCC}},
    gerbil_ld = {{GERBIL_LD}},
    gerbil_gsc = "gerbil-gsc",
    gxc = ":gxc",
    gxi = ":gxi",
    gxpkg = ":gxpkg",
    gxtest = ":gxtest",
    native_abi_fingerprint = {{NATIVE_ABI}},
    native_abi_fingerprint_file = "native_abi.txt",
    native_scheme_env = ":native_scheme_env",
    receipt = "toolchain.receipt.json",
    system_cpu_count = {{SYSTEM_CPU_COUNT}},
    system_memory_bytes = {{SYSTEM_MEMORY_BYTES}},
)

toolchain(
    name = "registered_toolchain",
    exec_compatible_with = {{EXEC_CONSTRAINTS}},
    toolchain = ":toolchain_impl",
    toolchain_type = "@gerbil_bazel//gerbil:toolchain_type",
)
