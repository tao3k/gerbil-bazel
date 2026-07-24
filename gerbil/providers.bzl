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

GerbilAotObjectInfo = provider(
    doc = "Declared native objects compiled from one explicit Gerbil package module.",
    fields = {
        "generated_c": "depset of generated module and Gambit linker C files",
        "link_object": "Gambit linker object for the compiled module set",
        "log": "AOT compiler operation log",
        "module": "canonical Gerbil module identifier",
        "module_objects": "depset of module and explicit native source objects",
        "receipt": "deterministic AOT compilation receipt",
    },
)

GerbilNativeLinkPlanInfo = provider(
    doc = "Ordered native link capability produced by Gerbil AOT compilation.",
    fields = {
        "link_inputs": "depset of native runtime libraries required by the plan",
        "link_libraries": "ordered native library projection",
        "link_object": "Gambit linker object",
        "link_search_roots": "depset of root markers for native link search directories",
        "module_objects": "depset of Gerbil and explicit native source objects",
        "plan": "machine-readable native link plan",
        "receipt": "deterministic AOT compilation receipt",
    },
)
