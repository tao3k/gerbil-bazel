"""Stable public toolchain API for Gerbil Bazel consumers."""
load(
    ":toolchain.bzl",
    _GERBIL_TOOLCHAIN_TYPE = "GERBIL_TOOLCHAIN_TYPE",
    _GerbilToolchainInfo = "GerbilToolchainInfo",
    _resolved_gerbil_toolchain = "resolved_gerbil_toolchain",
)

GERBIL_TOOLCHAIN_TYPE = _GERBIL_TOOLCHAIN_TYPE
GerbilToolchainInfo = _GerbilToolchainInfo
resolved_gerbil_toolchain = _resolved_gerbil_toolchain
