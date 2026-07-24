"""Stable public API for Gerbil Bazel consumers."""

load(":providers.bzl", _GerbilPackageInfo = "GerbilPackageInfo")
load(":test.bzl", _gerbil_test = "gerbil_test")
load(
    ":toolchain.bzl",
    _GERBIL_TOOLCHAIN_TYPE = "GERBIL_TOOLCHAIN_TYPE",
    _GerbilToolchainInfo = "GerbilToolchainInfo",
    _resolved_gerbil_toolchain = "resolved_gerbil_toolchain",
)

GERBIL_TOOLCHAIN_TYPE = _GERBIL_TOOLCHAIN_TYPE
GerbilPackageInfo = _GerbilPackageInfo
GerbilToolchainInfo = _GerbilToolchainInfo
gerbil_test = _gerbil_test
resolved_gerbil_toolchain = _resolved_gerbil_toolchain
