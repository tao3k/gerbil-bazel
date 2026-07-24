"""Gerbil-native package graph lowering for one hermetic source closure."""

load("//gerbil:repository_validation.bzl", "require_hex_digest")

_MANIFEST_SCHEMA = "gerbil-bazel.package-manifest.v1"
_GRAPH_SCHEMA = "gerbil-bazel.package-graph.v1"

def _safe_relative_path(value, field):
    if not value:
        fail("{} must not be empty".format(field))
    if value.startswith("/"):
        fail("{} must be relative, got {}".format(field, value))
    for part in value.split("/"):
        if part in ["", ".", ".."]:
            fail("{} must be a safe relative path, got {}".format(field, value))
    return value

def _path_fragment(index, value):
    return "{}_{}".format(
        index,
        value.replace("/", "_").replace(".", "_").replace("-", "_").replace("@", "_"),
    )

def _run_evaluator(repository_ctx, manifest_path):
    result = repository_ctx.execute(
        [
            repository_ctx.path(repository_ctx.attr.gxi),
            repository_ctx.path(repository_ctx.attr.evaluator),
            manifest_path,
        ],
        environment = repository_ctx.attr.environment,
        quiet = True,
    )
    if result.return_code != 0:
        fail("Gerbil package manifest evaluation failed for {}:\n{}".format(
            manifest_path,
            result.stderr,
        ))
    manifest = json.decode(result.stdout)
    if type(manifest) != "dict":
        fail("Gerbil package evaluator did not emit one JSON object: {}".format(manifest_path))
    if manifest.get("schema") != _MANIFEST_SCHEMA:
        fail("unsupported Gerbil package manifest schema for {}: {}".format(
            manifest_path,
            manifest.get("schema"),
        ))
    if manifest.get("manifest") != "gerbil.pkg":
        fail("Gerbil package evaluator returned a noncanonical manifest name: {}".format(
            manifest.get("manifest"),
        ))
    return manifest

def _validate_sources(manifest):
    seen = {}
    previous = None
    for source in manifest.get("sources", []):
        if type(source) != "dict":
            fail("package {} contains a non-object source entry".format(manifest["package"]))
        relative = _safe_relative_path(source.get("path", ""), "source path")
        require_hex_digest(source.get("sha256", ""), 64, "source sha256")
        if previous != None and relative <= previous:
            fail("package {} sources are not strictly sorted: {}".format(
                manifest["package"],
                relative,
            ))
        if relative in seen:
            fail("package {} contains duplicate source path {}".format(
                manifest["package"],
                relative,
            ))
        seen[relative] = True
        previous = relative
    if "gerbil.pkg" not in seen:
        fail("package {} closure is missing gerbil.pkg".format(manifest["package"]))
    if "build.ss" not in seen:
        fail("package {} closure is missing internal upstream builder".format(manifest["package"]))
    require_hex_digest(manifest.get("closureSha256", ""), 64, "closureSha256")

def _acquire_dependencies(repository_ctx):
    references = sorted(repository_ctx.attr.dependency_sha256.keys())
    if references != sorted(repository_ctx.attr.dependency_packages.keys()):
        fail("dependency_packages keys must exactly match dependency_sha256 keys")
    if references != sorted(repository_ctx.attr.dependency_revisions.keys()):
        fail("dependency_revisions keys must exactly match dependency_sha256 keys")
    if references != sorted(repository_ctx.attr.dependency_urls.keys()):
        fail("dependency_urls keys must exactly match dependency_sha256 keys")
    for reference in repository_ctx.attr.dependency_strip_prefixes.keys():
        if reference not in repository_ctx.attr.dependency_sha256:
            fail("dependency_strip_prefixes contains unknown reference {}".format(reference))

    records = []
    for index, reference in enumerate(references):
        _safe_relative_path(reference, "dependency reference")
        expected_package = _safe_relative_path(
            repository_ctx.attr.dependency_packages[reference],
            "dependency package",
        )
        urls = repository_ctx.attr.dependency_urls[reference]
        if not urls:
            fail("dependency {} must contain at least one source URL".format(reference))
        sha256 = require_hex_digest(
            repository_ctx.attr.dependency_sha256[reference],
            64,
            "dependency sha256",
        )
        source_root = repository_ctx.path(
            "_archives/{}".format(_path_fragment(index, reference)),
        )
        repository_ctx.download_and_extract(
            url = urls,
            output = source_root,
            canonical_id = "sha256:{}".format(sha256),
            sha256 = sha256,
            stripPrefix = repository_ctx.attr.dependency_strip_prefixes.get(reference, ""),
        )
        manifest_path = repository_ctx.path(str(source_root) + "/gerbil.pkg")
        manifest = _run_evaluator(repository_ctx, manifest_path)
        if manifest["package"] != expected_package:
            fail("dependency {} resolved package {} but lock declares {}".format(
                reference,
                manifest["package"],
                expected_package,
            ))
        _validate_sources(manifest)
        records.append(struct(
            acquisition = {
                "kind": "archive",
                "sha256": sha256,
                "stripPrefix": repository_ctx.attr.dependency_strip_prefixes.get(reference, ""),
                "urls": urls,
            },
            manifest = manifest,
            reference = reference,
            revision = repository_ctx.attr.dependency_revisions[reference],
            source_root = source_root,
        ))
    return records

def _reachable_records(root, dependencies):
    records_by_reference = {"//root": root}
    references_by_package = {root.manifest["package"]: "//root"}
    for dependency in dependencies:
        if dependency.reference in records_by_reference:
            fail("duplicate dependency reference {}".format(dependency.reference))
        previous_reference = references_by_package.get(dependency.manifest["package"])
        if previous_reference != None:
            fail("duplicate Gerbil package identity {} is locked by {} and {}".format(
                dependency.manifest["package"],
                previous_reference,
                dependency.reference,
            ))
        records_by_reference[dependency.reference] = dependency
        references_by_package[dependency.manifest["package"]] = dependency.reference

    reachable = {"//root": True}
    pending = ["//root"]
    for _ in range(len(records_by_reference) + 1):
        if not pending:
            break
        next_pending = []
        for reference in pending:
            record = records_by_reference[reference]
            for edge in record.manifest["dependencies"]:
                dependency_reference = edge["package"]
                dependency = records_by_reference.get(dependency_reference)
                if dependency == None:
                    fail("package {} has no locked dependency source for {}".format(
                        record.manifest["package"],
                        dependency_reference,
                    ))
                declared_revision = dependency.revision
                edge_revision = edge.get("tag") or ""
                if declared_revision != edge_revision:
                    fail("dependency {} revision mismatch: gerbil.pkg={}, lock={}".format(
                        dependency_reference,
                        edge_revision,
                        declared_revision,
                    ))
                if dependency_reference not in reachable:
                    reachable[dependency_reference] = True
                    next_pending.append(dependency_reference)
        pending = next_pending
    if pending:
        fail("Gerbil dependency closure expansion did not converge")

    extras = sorted([
        reference
        for reference in records_by_reference.keys()
        if reference not in reachable
    ])
    if extras:
        fail("dependency locks are not reachable from root gerbil.pkg: {}".format(extras))
    return records_by_reference

def _topological_references(records_by_reference):
    remaining = {reference: True for reference in records_by_reference.keys()}
    emitted = {}
    result = []
    for _ in range(len(records_by_reference)):
        ready = []
        for reference in sorted(remaining.keys()):
            dependencies = [
                edge["package"]
                for edge in records_by_reference[reference].manifest["dependencies"]
            ]
            if all([dependency in emitted for dependency in dependencies]):
                ready.append(reference)
        if not ready:
            fail("Gerbil package dependency graph contains a cycle: {}".format(
                sorted(remaining.keys()),
            ))
        for reference in ready:
            remaining.pop(reference)
            emitted[reference] = True
            result.append(reference)
    return result

def _materialize_sources(repository_ctx, records_by_reference):
    target_names = {}
    package_roots = {}
    all_labels = []
    for index, reference in enumerate(sorted(records_by_reference.keys())):
        record = records_by_reference[reference]
        target_name = "package_{}".format(index)
        package_root = "packages/{}".format(_path_fragment(index, record.manifest["package"]))
        target_names[reference] = target_name
        package_roots[reference] = package_root
        for source in record.manifest["sources"]:
            relative = source["path"]
            destination = "{}/{}".format(package_root, relative)
            repository_ctx.symlink(
                repository_ctx.path(str(record.source_root) + "/" + relative),
                destination,
            )
            all_labels.append(destination)
    return struct(
        all_labels = sorted(all_labels),
        package_roots = package_roots,
        target_names = target_names,
    )

def _quote(value):
    return json.encode(value)

def _render_string_list(values, indent):
    return "".join([
        "{}{},\n".format(indent, _quote(value))
        for value in values
    ])

def _write_build(repository_ctx, records_by_reference, layout):
    package_targets = []
    for reference in _topological_references(records_by_reference):
        record = records_by_reference[reference]
        package_root = layout.package_roots[reference]
        source_labels = [
            "{}/{}".format(package_root, source["path"])
            for source in record.manifest["sources"]
            if source["path"] != "gerbil.pkg"
        ]
        dependency_labels = [
            ":{}".format(layout.target_names[edge["package"]])
            for edge in record.manifest["dependencies"]
        ]
        dependency_references = [
            edge["package"]
            for edge in record.manifest["dependencies"]
        ]
        package_targets.append("""
gerbil_package(
    name = {name},
    dependency_references = [
{dependency_references}    ],
    deps = [
{deps}    ],
    manifest = {manifest},
    package_identity = {package_identity},
    package_reference = {package_reference},
    package_revision = {package_revision},
    srcs = [
{srcs}    ],
)
""".format(
            dependency_references = _render_string_list(dependency_references, "        "),
            deps = _render_string_list(dependency_labels, "        "),
            manifest = _quote("{}/gerbil.pkg".format(package_root)),
            name = _quote(layout.target_names[reference]),
            package_identity = _quote(record.manifest["package"]),
            package_reference = _quote(
                record.manifest["package"] if reference == "//root" else reference,
            ),
            package_revision = _quote(record.revision),
            srcs = _render_string_list(source_labels, "        "),
        ))

    repository_ctx.file("BUILD.bazel", """load("@gerbil_bazel//gerbil:package.bzl", "gerbil_package")

package(default_visibility = ["//visibility:private"])

exports_files(
    ["package-graph.json"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "source_closure",
    srcs = [
{all_sources}    ],
    visibility = ["//visibility:public"],
)
{package_targets}
alias(
    name = "build",
    actual = {root_target},
    visibility = ["//visibility:public"],
)

filegroup(
    name = "build_receipt",
    srcs = [{root_target}],
    output_group = "receipt",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "gxpkg_manifest",
    srcs = [{root_target}],
    output_group = "gxpkg_manifest",
    visibility = ["//visibility:public"],
)
""".format(
        all_sources = _render_string_list(layout.all_labels, "        "),
        package_targets = "".join(package_targets),
        root_target = _quote(":{}".format(layout.target_names["//root"])),
    ))

def _package_graph_repository_impl(repository_ctx):
    root_manifest = repository_ctx.path(repository_ctx.attr.root_manifest)
    root_source = root_manifest.dirname
    repository_ctx.watch_tree(root_source)
    root_manifest_json = _run_evaluator(repository_ctx, root_manifest)
    _validate_sources(root_manifest_json)
    root = struct(
        acquisition = {
            "kind": "workspace",
        },
        manifest = root_manifest_json,
        reference = "//root",
        revision = repository_ctx.attr.root_revision,
        source_root = root_source,
    )
    dependencies = _acquire_dependencies(repository_ctx)
    records_by_reference = _reachable_records(root, dependencies)
    layout = _materialize_sources(repository_ctx, records_by_reference)
    receipt_packages = []
    for reference in sorted(records_by_reference.keys()):
        record = records_by_reference[reference]
        receipt_packages.append({
            "acquisition": record.acquisition,
            "manifest": record.manifest,
            "reference": reference,
            "revision": record.revision,
            "target": "//:{}".format(layout.target_names[reference]),
        })
    repository_ctx.file(
        "package-graph.json",
        json.encode_indent({
            "packages": receipt_packages,
            "rootPackage": root.manifest["package"],
            "schema": _GRAPH_SCHEMA,
        }) + "\n",
    )
    _write_build(repository_ctx, records_by_reference, layout)

package_graph_repository = repository_rule(
    implementation = _package_graph_repository_impl,
    attrs = {
        "dependency_packages": attr.string_dict(),
        "dependency_revisions": attr.string_dict(),
        "dependency_sha256": attr.string_dict(),
        "dependency_strip_prefixes": attr.string_dict(),
        "dependency_urls": attr.string_list_dict(),
        "environment": attr.string_dict(),
        "evaluator": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:package_manifest.ss",
        ),
        "gxi": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "root_manifest": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "root_revision": attr.string(),
    },
)
