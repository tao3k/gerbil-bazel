"""Stable public API for Gerbil Bazel consumers."""

load(
    ":project.bzl",
    _GerbilProjectInfo = "GerbilProjectInfo",
    _gerbil_project_compile = "gerbil_project_compile",
    _gerbil_project_dev = "gerbil_project_dev",
    _gerbil_project_test = "gerbil_project_test",
)
load(
    ":toolchain.bzl",
    _GERBIL_TOOLCHAIN_TYPE = "GERBIL_TOOLCHAIN_TYPE",
    _GerbilToolchainInfo = "GerbilToolchainInfo",
    _resolved_gerbil_toolchain = "resolved_gerbil_toolchain",
)

GERBIL_TOOLCHAIN_TYPE = _GERBIL_TOOLCHAIN_TYPE
GerbilProjectInfo = _GerbilProjectInfo
GerbilToolchainInfo = _GerbilToolchainInfo
gerbil_project_compile = _gerbil_project_compile
gerbil_project_dev = _gerbil_project_dev
gerbil_project_test = _gerbil_project_test
resolved_gerbil_toolchain = _resolved_gerbil_toolchain
