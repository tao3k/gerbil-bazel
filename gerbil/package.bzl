"""Private Bazel action used by generated Gerbil package graphs."""

load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

GerbilPackageInfo = provider(
    doc = "Outputs carried between generated Gerbil package targets.",
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

def _staged_path(path):
    if path.startswith("../"):
        return ".gerbil-bazel/external/" + path[3:]
    if path.startswith(".gerbil-bazel/"):
        fail("package source path uses reserved staging namespace: {}".format(path))
    return path

def _source_entries(files):
    sources_by_destination = {}
    for file in files:
        destination = _staged_path(file.short_path)
        previous = sources_by_destination.get(destination)
        if previous != None:
            fail("staged package source collision at {}: {} and {}".format(
                destination,
                previous,
                file.path,
            ))
        sources_by_destination[destination] = file.path
    return [
        {
            "destination": destination,
            "source": sources_by_destination[destination],
        }
        for destination in sorted(sources_by_destination.keys())
    ]

def _direct_dependencies(ctx, package_dependencies):
    if len(ctx.attr.dependency_references) != len(package_dependencies):
        fail("{} has {} dependency references but {} package dependencies".format(
            ctx.label,
            len(ctx.attr.dependency_references),
            len(package_dependencies),
        ))
    entries = []
    for index in range(len(package_dependencies)):
        dependency = package_dependencies[index]
        reference = ctx.attr.dependency_references[index]
        if dependency.package_reference != reference:
            fail("{} dependency {} resolves reference {} but edge declares {}".format(
                ctx.label,
                dependency.package_identity,
                dependency.package_reference,
                reference,
            ))
        entries.append({
            "manifest": dependency.gxpkg_manifest.path,
            "reference": reference,
        })
    return entries

def _gerbil_package_impl(ctx):
    toolchain = resolved_gerbil_toolchain(ctx)
    package_dependencies = [dep[GerbilPackageInfo] for dep in ctx.attr.deps]
    direct_dependencies = _direct_dependencies(ctx, package_dependencies)
    dependency_roots = depset(
        direct = [dependency.package_root for dependency in package_dependencies],
        order = "postorder",
        transitive = [dependency.dependency_roots for dependency in package_dependencies],
    )
    package_root = ctx.actions.declare_directory(ctx.label.name + ".package")
    gxpkg_manifest = ctx.actions.declare_file(ctx.label.name + ".gxpkg-manifest")
    receipt = ctx.actions.declare_file(ctx.label.name + ".receipt.json")
    log = ctx.actions.declare_file(ctx.label.name + ".log")
    request = ctx.actions.declare_file(ctx.label.name + ".request.json")
    sources = depset(direct = [ctx.file.manifest] + ctx.files.srcs)
    ctx.actions.write(
        output = request,
        content = json.encode({
            "args": ctx.attr.args,
            "dependencyRootMarker": toolchain.dependency_library_root.path,
            "gxpkgManifest": gxpkg_manifest.path,
            "log": log.path,
            "manifest": _staged_path(ctx.file.manifest.short_path),
            "packageDependencies": direct_dependencies,
            "packageDependencyRoots": [
                root.path
                for root in dependency_roots.to_list()
            ],
            "packageIdentity": ctx.attr.package_identity,
            "packageLabel": str(ctx.label),
            "packageReference": ctx.attr.package_reference,
            "packageRevision": ctx.attr.package_revision,
            "packageRoot": package_root.path,
            "processGuard": ctx.attr.process_guard,
            "processGuardTimeoutSeconds": ctx.attr.process_guard_timeout_seconds,
            "receipt": receipt.path,
            "requireLibraryOutput": ctx.attr.require_library_output,
            "schema": "gerbil-bazel.package-request.v1",
            "sources": _source_entries(sources.to_list()),
            "tools": {
                "as": toolchain.gerbil_as,
                "cc": toolchain.gerbil_cc,
                "gxc": toolchain.gxc.executable.path,
                "gxi": toolchain.gxi.executable.path,
                "gxpkg": toolchain.gxpkg.executable.path,
                "ld": toolchain.gerbil_ld,
            },
        }) + "\n",
    )
    args = ctx.actions.args()
    args.add(ctx.file._runner.path)
    args.add(request.path)
    environment = dict(toolchain.environment)
    environment.update(ctx.attr.env)
    environment["CC"] = toolchain.gerbil_cc
    environment["GERBIL_BAZEL_NATIVE_ABI"] = toolchain.native_abi_fingerprint
    ctx.actions.run(
        arguments = [args],
        env = environment,
        executable = toolchain.gxi,
        inputs = depset(
            direct = [
                ctx.file._functional,
                ctx.file._resource_policy,
                ctx.file._runner,
                request,
                toolchain.dependency_library_root,
                toolchain.native_abi_fingerprint_file,
            ] + [
                dependency.gxpkg_manifest
                for dependency in package_dependencies
            ],
            transitive = [
                sources,
                dependency_roots,
                toolchain.dependency_libraries,
                toolchain.compile_runfiles,
            ],
        ),
        mnemonic = "GerbilPackageBuild",
        outputs = [package_root, gxpkg_manifest, receipt, log],
        progress_message = "Building Gerbil package %{label}",
        tools = [
            toolchain.gxi,
            toolchain.gxc,
            toolchain.gxpkg,
        ],
    )
    info = GerbilPackageInfo(
        dependency_roots = dependency_roots,
        gxpkg_manifest = gxpkg_manifest,
        log = log,
        package_identity = ctx.attr.package_identity,
        package_reference = ctx.attr.package_reference,
        package_root = package_root,
        receipt = receipt,
    )
    return [
        DefaultInfo(files = depset([package_root, gxpkg_manifest, receipt, log])),
        info,
        OutputGroupInfo(
            gxpkg_manifest = depset([gxpkg_manifest]),
            log = depset([log]),
            package_root = depset([package_root]),
            receipt = depset([receipt]),
        ),
    ]

gerbil_package = rule(
    implementation = _gerbil_package_impl,
    attrs = {
        "args": attr.string_list(),
        "dependency_references": attr.string_list(),
        "deps": attr.label_list(providers = [GerbilPackageInfo]),
        "env": attr.string_dict(),
        "manifest": attr.label(allow_single_file = True, mandatory = True),
        "package_identity": attr.string(mandatory = True),
        "package_reference": attr.string(mandatory = True),
        "package_revision": attr.string(),
        "process_guard": attr.bool(default = True),
        "process_guard_timeout_seconds": attr.int(default = 0),
        "require_library_output": attr.bool(default = False),
        "srcs": attr.label_list(allow_files = True),
        "_functional": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:functional.ss",
        ),
        "_resource_policy": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:resource_policy.ss",
        ),
        "_runner": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:package_runner.ss",
        ),
    },
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)
