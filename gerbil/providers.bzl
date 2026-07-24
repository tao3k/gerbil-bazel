"""Stable public providers for Gerbil package consumers."""

GerbilPackageInfo = provider(
    doc = "Built Gerbil package capability carried by generated package graph targets.",
    fields = {
        "dependency_roots": "transitive depset of built dependency package roots",
        "gxpkg_manifest": "plain upstream-compatible gxpkg dependency manifest",
        "log": "complete package build log",
        "package_identity": "identity declared by this package's gerbil.pkg",
        "package_reference": "graph reference used by parent gerbil.pkg manifests",
        "package_root": "tree artifact containing the isolated built package",
        "receipt": "machine-readable package build receipt",
    },
)
