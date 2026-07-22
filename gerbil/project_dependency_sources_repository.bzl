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
        if relative.startswith(".git/") or "/.git/" in relative:
            continue
        files.append(relative)
    return sorted(files)

def _quote(value):
    return json.encode(value)

def _project_dependency_sources_repository_impl(repository_ctx):
    package = _safe_relative_path(repository_ctx.attr.package, "package")
    project_library_relative_path = _safe_relative_path(
        repository_ctx.attr.project_library_relative_path,
        "project_library_relative_path",
    )
    project_root = repository_ctx.path(repository_ctx.attr.project_root_marker).dirname
    library_root = str(project_root) + "/" + project_library_relative_path
    package_checkout_root = str(project_root) + "/.gerbil/pkg"
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
    package_root = None
    for root in [package_checkout_root, library_root]:
        for candidate in candidates:
            candidate_root = repository_ctx.path(root + "/" + candidate)
            if candidate_root.exists:
                package_root = candidate_root
                break
        if package_root != None:
            break
    if package_root == None:
        fail("project dependency package does not exist: {}".format(package))

    repository_ctx.watch_tree(package_root)
    source_files = _source_files(repository_ctx, package_root)
    if not source_files:
        fail("project dependency package has no source files: {}".format(package))
    for source_file in source_files:
        repository_ctx.symlink(
            repository_ctx.path(str(package_root) + "/" + source_file),
            "src/" + source_file,
        )
    build_script = repository_ctx.path(str(package_root) + "/build.ss")
    if build_script.exists:
        repository_ctx.symlink(build_script, "build.ss")
    else:
        repository_ctx.file("build.ss", "; generated empty build script for package without build.ss\n")
    source_labels = ["src/" + source_file for source_file in source_files]
    repository_ctx.file("BUILD.bazel", """
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
""".format(
        source_labels = "".join(["        {},\n".format(_quote(label)) for label in source_labels]),
    ))

project_dependency_sources_repository = repository_rule(
    implementation = _project_dependency_sources_repository_impl,
    attrs = {
        "package": attr.string(mandatory = True),
        "project_library_relative_path": attr.string(default = ".gerbil/lib"),
        "project_root_marker": attr.label(allow_single_file = True, mandatory = True),
    },
)
