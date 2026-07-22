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
    repository_ctx.symlink(package_root, "src")
    build_script = repository_ctx.path(str(package_root) + "/build.ss")
    if build_script.exists:
        repository_ctx.symlink(build_script, "build.ss")
    else:
        repository_ctx.file("build.ss", "; generated empty build script for package without build.ss\n")
    repository_ctx.file("BUILD.bazel", """
filegroup(
    name = "sources",
    srcs = glob(["src/**"], exclude = ["src/BUILD", "src/BUILD.bazel"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "build_script",
    srcs = ["build.ss"],
    visibility = ["//visibility:public"],
)
""")

project_dependency_sources_repository = repository_rule(
    implementation = _project_dependency_sources_repository_impl,
    attrs = {
        "package": attr.string(mandatory = True),
        "project_library_relative_path": attr.string(default = ".gerbil/lib"),
        "project_root_marker": attr.label(allow_single_file = True, mandatory = True),
    },
)
