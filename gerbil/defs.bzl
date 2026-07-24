"""Stable public API for Gerbil Bazel consumers."""

load(":aot.bzl", _gerbil_aot_objects = "gerbil_aot_objects")
load(":binary.bzl", _gerbil_package_binary = "gerbil_package_binary")
load(
    ":providers.bzl",
    _GerbilAotObjectInfo = "GerbilAotObjectInfo",
    _GerbilNativeLinkPlanInfo = "GerbilNativeLinkPlanInfo",
    _GerbilPackageInfo = "GerbilPackageInfo",
)
load(":test.bzl", _gerbil_test = "gerbil_test")
load(
    ":toolchain.bzl",
    _GERBIL_TOOLCHAIN_TYPE = "GERBIL_TOOLCHAIN_TYPE",
    _GerbilToolchainInfo = "GerbilToolchainInfo",
    _resolved_gerbil_toolchain = "resolved_gerbil_toolchain",
)

GERBIL_TOOLCHAIN_TYPE = _GERBIL_TOOLCHAIN_TYPE
GerbilAotObjectInfo = _GerbilAotObjectInfo
GerbilNativeLinkPlanInfo = _GerbilNativeLinkPlanInfo
GerbilPackageInfo = _GerbilPackageInfo
GerbilToolchainInfo = _GerbilToolchainInfo
gerbil_aot_objects = _gerbil_aot_objects
gerbil_package_binary = _gerbil_package_binary
gerbil_test = _gerbil_test
resolved_gerbil_toolchain = _resolved_gerbil_toolchain
