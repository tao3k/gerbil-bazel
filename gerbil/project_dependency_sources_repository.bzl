def _safe_relative_path(value, field):
    if not value:
        fail("{} must not be empty".format(field))
    if value.startswith("/"):
        fail("{} must be relative, got {}".format(field, value))
    parts = value.split("/")
    for part in parts:
        if part == "" or part == "." or part == "..":
            fail("{} must be a safe relative path, got {}".format(field, value))
    return value

def _source_files(repository_ctx, root):
    result = repository_ctx.execute([
        "find",
        str(root),
        "-type",
        "f",
    ], quiet = True)
    if result.return_code != 0:
        fail("failed to enumerate project dependency sources: {}".format(result.stderr))

    root_prefix = str(root) + "/"
    files = []
    for line in result.stdout.splitlines():
        if not line.startswith(root_prefix):
            continue
        relative = line[len(root_prefix):]
        if relative in ["BUILD", "BUILD.bazel"]:
            continue
        if relative.endswith("/BUILD") or relative.endswith("/BUILD.bazel"):
            continue
        if relative.startswith(".git/") or "/.git/" in relative:
            continue
        files.append(relative)
    return sorted(files)

def _quote(value):
    return json.encode(value)

def _fail_resolution(
        package,
        outcome,
        diagnostic,
        resolution_mode,
        canonical_package_path = "",
        canonical_uri = "",
        expected_revision = "",
        observed_revision = "",
        source_snapshot_digest = "",
        candidates = []):
    receipt = {
        "schema": "gerbil-bazel.dependency-source-resolution-receipt.v1",
        "logicalPackage": package,
        "resolutionMode": resolution_mode,
        "canonicalPackagePath": canonical_package_path,
        "canonicalUri": canonical_uri,
        "expectedRevision": expected_revision,
        "observedRevision": observed_revision,
        "sourceSnapshotDigest": source_snapshot_digest,
        "sourceFileCount": 0,
        "worktreeDirty": False,
        "candidates": candidates,
        "outcome": outcome,
        "diagnostic": diagnostic,
    }
    fail("SOURCE_RESOLUTION_RECEIPT " + json.encode(receipt))

def _command_output(repository_ctx, argv, error_message):
    result = repository_ctx.execute(argv, quiet = True)
    if result.return_code != 0:
        fail("{}: {}".format(error_message, result.stderr.strip()))
    return result.stdout.strip()

def _normalized_git_uri(value):
    normalized = value.strip()
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized[len("git@github.com:"):]
    if normalized.endswith(".git"):
        normalized = normalized[:-len(".git")]
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized

def _git_metadata(repository_ctx, root, revision = "HEAD"):
    git_root_result = repository_ctx.execute(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        quiet = True,
    )
    if git_root_result.return_code != 0:
        return None
    git_root = git_root_result.stdout.strip()
    package_prefix_result = repository_ctx.execute(
        ["git", "-C", str(root), "rev-parse", "--show-prefix"],
        quiet = True,
    )
    if package_prefix_result.return_code != 0:
        return None
    package_relative_path = package_prefix_result.stdout.strip()
    if package_relative_path.endswith("/"):
        package_relative_path = package_relative_path[:-1]

    commit_result = repository_ctx.execute(
        ["git", "-C", git_root, "rev-parse", revision + "^{commit}"],
        quiet = True,
    )
    if commit_result.return_code != 0:
        return None
    tree_revision = revision + "^{tree}"
    if package_relative_path:
        tree_revision = revision + ":" + package_relative_path
    tree = _command_output(
        repository_ctx,
        ["git", "-C", git_root, "rev-parse", tree_revision],
        "failed to resolve dependency source tree",
    )
    remote_result = repository_ctx.execute(
        ["git", "-C", git_root, "remote", "get-url", "origin"],
        quiet = True,
    )
    dirty_argv = ["git", "-C", git_root, "status", "--porcelain"]
    if package_relative_path:
        dirty_argv += ["--", package_relative_path]
    dirty_result = repository_ctx.execute(
        dirty_argv,
        quiet = True,
    )
    return struct(
        commit = commit_result.stdout.strip(),
        dirty = dirty_result.return_code == 0 and bool(dirty_result.stdout.strip()),
        git_root = git_root,
        package_relative_path = package_relative_path,
        remote = remote_result.stdout.strip() if remote_result.return_code == 0 else "",
        tree = tree,
    )

def _remove_nested_build_files(repository_ctx, root):
    result = repository_ctx.execute([
        "find",
        str(root),
        "-type",
        "f",
        "(",
        "-name",
        "BUILD",
        "-o",
        "-name",
        "BUILD.bazel",
        ")",
        "-delete",
    ], quiet = True)
    if result.return_code != 0:
        fail("failed to remove nested BUILD files from dependency snapshot: {}".format(
            result.stderr,
        ))

def _materialize_revision(
        repository_ctx,
        package,
        package_root,
        canonical_package_path,
        canonical_uri,
        expected_revision):
    metadata = _git_metadata(repository_ctx, package_root, expected_revision)
    if metadata == None:
        diagnostic = "project dependency revision is unavailable: {}".format(
            expected_revision,
        )
        _fail_resolution(
            package,
            "revision-mismatch",
            diagnostic,
            "identified-revision",
            canonical_package_path = canonical_package_path,
            canonical_uri = canonical_uri,
            expected_revision = expected_revision,
        )
    if metadata.commit != expected_revision:
        diagnostic = "project dependency revision mismatch: expected {}, resolved {}".format(
            expected_revision,
            metadata.commit,
        )
        _fail_resolution(
            package,
            "revision-mismatch",
            diagnostic,
            "identified-revision",
            canonical_package_path = canonical_package_path,
            canonical_uri = canonical_uri,
            expected_revision = expected_revision,
            observed_revision = metadata.commit,
            source_snapshot_digest = metadata.tree,
        )

    archive = repository_ctx.path("_dependency-source-snapshot.tar")
    archive_argv = [
        "git",
        "-C",
        metadata.git_root,
        "archive",
        "--format=tar",
        "--output",
        str(archive),
        expected_revision,
    ]
    if metadata.package_relative_path:
        archive_argv.append(metadata.package_relative_path)
    archive_result = repository_ctx.execute(archive_argv, quiet = True)
    if archive_result.return_code != 0:
        fail("failed to archive dependency source revision {}: {}".format(
            expected_revision,
            archive_result.stderr,
        ))
    extract_argv = [
        "tar",
        "-xf",
        str(archive),
        "-C",
        str(repository_ctx.path(".")),
    ]
    if metadata.package_relative_path:
        extract_argv += [
            "--strip-components",
            str(len(metadata.package_relative_path.split("/"))),
        ]
    extract_result = repository_ctx.execute(extract_argv, quiet = True)
    repository_ctx.delete(archive)
    if extract_result.return_code != 0:
        fail("failed to extract dependency source revision {}: {}".format(
            expected_revision,
            extract_result.stderr,
        ))
    _remove_nested_build_files(repository_ctx, repository_ctx.path("."))
    return metadata

def _legacy_source_candidate(repository_ctx, package_checkout_root, library_root, package):
    candidates = [package]
    known_github_packages = {
        "gerbil-utils": [
            "github.com/tao3k/gerbil-utils",
            "github.com/mighty-gerbils/gerbil-utils",
        ],
        "gerbil-poo": [
            "github.com/tao3k/gerbil-poo",
            "github.com/mighty-gerbils/gerbil-poo",
        ],
        "gslph": ["github.com/tao3k/gerbil-scheme-language-project-harness"],
    }
    candidates += known_github_packages.get(package, [])

    existing = []
    matches = []
    seen = {}
    for root_kind, root in [
        ("checkout", package_checkout_root),
        ("library", library_root),
    ]:
        for candidate in candidates:
            candidate_root = repository_ctx.path(root + "/" + candidate)
            candidate_key = str(candidate_root)
            if candidate_key in seen:
                continue
            seen[candidate_key] = True
            if not candidate_root.exists:
                continue
            label = "{}:{}".format(root_kind, candidate)
            existing.append(label)
            source_files = _source_files(repository_ctx, candidate_root)
            if source_files:
                matches.append(struct(
                    label = label,
                    root = candidate_root,
                    source_files = source_files,
                ))

    if not matches:
        if existing:
            diagnostic = "project dependency package has no source files: {}; candidates={}".format(
                package,
                ",".join(existing),
            )
            _fail_resolution(
                package,
                "compiled-artifact-only",
                diagnostic,
                "legacy-candidate-selection",
                candidates = existing,
            )
        diagnostic = "project dependency package does not exist: {}".format(package)
        _fail_resolution(
            package,
            "missing",
            diagnostic,
            "legacy-candidate-selection",
        )
    if len(matches) != 1:
        candidate_labels = [match.label for match in matches]
        diagnostic = "project dependency source resolution is ambiguous: {}; candidates={}".format(
            package,
            ",".join(candidate_labels),
        )
        _fail_resolution(
            package,
            "ambiguous",
            diagnostic,
            "legacy-candidate-selection",
            candidates = candidate_labels,
        )
    return matches[0]

def _write_repository(
        repository_ctx,
        package,
        package_root,
        source_files,
        resolution_mode,
        canonical_package_path = "",
        canonical_uri = "",
        expected_revision = "",
        metadata = None):
    for source_file in source_files:
        source_path = repository_ctx.path(str(package_root) + "/" + source_file)
        target_path = repository_ctx.path(source_file)
        if source_path != target_path:
            repository_ctx.symlink(source_path, source_file)

    build_script = repository_ctx.path(str(package_root) + "/build.ss")
    if build_script.exists:
        if "build.ss" not in source_files:
            repository_ctx.symlink(build_script, "build.ss")
    else:
        repository_ctx.file("build.ss", "; generated empty build script for package without build.ss\n")

    receipt = {
        "schema": "gerbil-bazel.dependency-source-resolution-receipt.v1",
        "logicalPackage": package,
        "resolutionMode": resolution_mode,
        "canonicalPackagePath": canonical_package_path,
        "canonicalUri": canonical_uri,
        "expectedRevision": expected_revision,
        "observedRevision": metadata.commit if metadata != None else "",
        "sourceSnapshotDigest": metadata.tree if metadata != None else "",
        "sourceFileCount": len(source_files),
        "worktreeDirty": metadata.dirty if metadata != None else False,
        "outcome": "resolved",
    }
    repository_ctx.file(
        "source-resolution-receipt.json",
        json.encode(receipt) + "\n",
    )

    source_labels = source_files
    repository_ctx.file("BUILD.bazel", """
exports_files(
    [
{exported_source_labels}
        "source-resolution-receipt.json",
    ],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "sources",
    srcs = [
{source_labels}
    ],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "build_script",
    srcs = ["build.ss"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "source_resolution_receipt",
    srcs = ["source-resolution-receipt.json"],
    visibility = ["//visibility:public"],
)
""".format(
        exported_source_labels = "".join(["        {},\n".format(_quote(label)) for label in source_labels]),
        source_labels = "".join(["        {},\n".format(_quote(label)) for label in source_labels]),
    ))

def _project_dependency_sources_repository_impl(repository_ctx):
    package = _safe_relative_path(repository_ctx.attr.package, "package")
    project_library_relative_path = _safe_relative_path(
        repository_ctx.attr.project_library_relative_path,
        "project_library_relative_path",
    )
    project_root = repository_ctx.path(repository_ctx.attr.project_root_marker).dirname
    library_root = str(project_root) + "/" + project_library_relative_path
    package_checkout_root = str(project_root) + "/.gerbil/pkg"
    canonical_package_path = repository_ctx.attr.canonical_package_path
    if canonical_package_path:
        canonical_package_path = _safe_relative_path(
            canonical_package_path,
            "canonical_package_path",
        )
        expected_revision = repository_ctx.attr.expected_revision
        if not expected_revision:
            diagnostic = "expected_revision must not be empty for identified dependency source resolution"
            _fail_resolution(
                package,
                "revision-mismatch",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
            )
        canonical_uri = _normalized_git_uri(repository_ctx.attr.canonical_uri)
        if not canonical_uri:
            diagnostic = "canonical_uri must not be empty for identified dependency source resolution"
            _fail_resolution(
                package,
                "identity-mismatch",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
                expected_revision = expected_revision,
            )
        package_root = repository_ctx.path(
            str(project_root) + "/" + canonical_package_path,
        )
        if not package_root.exists:
            diagnostic = "identified dependency source checkout does not exist: {}".format(
                canonical_package_path,
            )
            _fail_resolution(
                package,
                "missing",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
                canonical_uri = canonical_uri,
                expected_revision = expected_revision,
            )
        observed_metadata = _git_metadata(repository_ctx, package_root)
        if observed_metadata == None:
            diagnostic = "identified dependency source is not a Git checkout: {}".format(
                canonical_package_path,
            )
            _fail_resolution(
                package,
                "identity-mismatch",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
                canonical_uri = canonical_uri,
                expected_revision = expected_revision,
            )
        if _normalized_git_uri(observed_metadata.remote) != canonical_uri:
            diagnostic = "identified dependency source URI mismatch: expected {}, observed {}".format(
                canonical_uri,
                _normalized_git_uri(observed_metadata.remote),
            )
            _fail_resolution(
                package,
                "identity-mismatch",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
                canonical_uri = canonical_uri,
                expected_revision = expected_revision,
                observed_revision = observed_metadata.commit,
                source_snapshot_digest = observed_metadata.tree,
            )
        metadata = _materialize_revision(
            repository_ctx,
            package,
            package_root,
            canonical_package_path,
            canonical_uri,
            expected_revision,
        )
        source_files = _source_files(repository_ctx, repository_ctx.path("."))
        if not source_files:
            diagnostic = "identified dependency revision has no source files: {}@{}".format(
                canonical_package_path,
                expected_revision,
            )
            _fail_resolution(
                package,
                "compiled-artifact-only",
                diagnostic,
                "identified-revision",
                canonical_package_path = canonical_package_path,
                canonical_uri = canonical_uri,
                expected_revision = expected_revision,
                observed_revision = metadata.commit,
                source_snapshot_digest = metadata.tree,
            )
        _write_repository(
            repository_ctx,
            package,
            repository_ctx.path("."),
            source_files,
            "identified-revision",
            canonical_package_path = canonical_package_path,
            canonical_uri = canonical_uri,
            expected_revision = expected_revision,
            metadata = metadata,
        )
        return

    match = _legacy_source_candidate(
        repository_ctx,
        package_checkout_root,
        library_root,
        package,
    )
    repository_ctx.watch_tree(match.root)
    _write_repository(
        repository_ctx,
        package,
        match.root,
        match.source_files,
        "legacy-unique-source",
        canonical_package_path = match.label,
        metadata = _git_metadata(repository_ctx, match.root),
    )

project_dependency_sources_repository = repository_rule(
    implementation = _project_dependency_sources_repository_impl,
    attrs = {
        "canonical_package_path": attr.string(),
        "canonical_uri": attr.string(),
        "expected_revision": attr.string(),
        "package": attr.string(mandatory = True),
        "project_library_relative_path": attr.string(default = ".gerbil/lib"),
        "project_root_marker": attr.label(allow_single_file = True, mandatory = True),
    },
)
