"""Hermetic source archives for Gerbil project dependencies."""

load("//gerbil:repository_validation.bzl", "require_hex_digest")

def _safe_relative_path(value, field):
    if not value:
        fail("{} must not be empty".format(field))
    if value.startswith("/"):
        fail("{} must be relative, got {}".format(field, value))
    for part in value.split("/"):
        if part in ["", ".", ".."]:
            fail("{} must be a safe relative path, got {}".format(field, value))
    return value

_MAX_SOURCE_DEPTH = 64
_RESERVED_TOP_LEVEL = ["_source", "source-package.json"]

def _normalized_path(path):
    return str(path).replace("\\", "/")

def _source_files(root):
    root_real = _normalized_path(root.realpath)
    files = []
    directories = [struct(path = root, relative = "")]
    for _depth in range(_MAX_SOURCE_DEPTH):
        if not directories:
            return sorted(files)
        next_directories = []
        for directory in directories:
            entries = {}
            for entry in directory.path.readdir(watch = "no"):
                entries[entry.basename] = entry
            for name in sorted(entries.keys()):
                entry = entries[name]
                relative = name if not directory.relative else directory.relative + "/" + name
                parts = relative.split("/")
                if ".git" in parts:
                    continue
                if parts[0] in _RESERVED_TOP_LEVEL:
                    fail("downloaded Gerbil package uses reserved path: {}".format(relative))
                expected_real = root_real + "/" + relative
                if _normalized_path(entry.realpath) != expected_real:
                    fail("downloaded Gerbil package symlinks are unsupported: {}".format(relative))
                if entry.is_dir:
                    next_directories.append(struct(path = entry, relative = relative))
                elif name not in ["BUILD", "BUILD.bazel"]:
                    files.append(relative)
        directories = next_directories
    fail("downloaded Gerbil package exceeds maximum source depth {}".format(_MAX_SOURCE_DEPTH))

def _quote(value):
    return json.encode(value)

def _source_package_repository_impl(repository_ctx):
    package = _safe_relative_path(repository_ctx.attr.package, "package")
    build_script = _safe_relative_path(repository_ctx.attr.build_script, "build_script")
    if not repository_ctx.attr.urls:
        fail("urls must contain at least one source archive URL")
    sha256 = require_hex_digest(repository_ctx.attr.sha256, 64, "sha256")
    source_root = repository_ctx.path("_source")
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.urls,
        output = source_root,
        canonical_id = "sha256:{}".format(sha256),
        sha256 = sha256,
        stripPrefix = repository_ctx.attr.strip_prefix,
    )

    source_files = _source_files(source_root)
    if not source_files:
        fail("downloaded Gerbil package has no source files: {}".format(package))
    if build_script not in source_files:
        fail("downloaded Gerbil package build script does not exist: {}".format(build_script))

    for source_file in source_files:
        repository_ctx.symlink(
            repository_ctx.path(str(source_root) + "/" + source_file),
            source_file,
        )

    repository_ctx.file(
        "source-package.json",
        json.encode_indent({
            "buildScript": build_script,
            "package": package,
            "sha256": sha256,
            "urls": repository_ctx.attr.urls,
        }) + "\n",
    )
    exported_files = source_files + ["source-package.json"]
    repository_ctx.file("BUILD.bazel", """
exports_files(
    [
{exported_source_labels}
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
    srcs = [{build_script}],
    visibility = ["//visibility:public"],
)
""".format(
        build_script = _quote(build_script),
        exported_source_labels = "".join([
            "        {},\n".format(_quote(label))
            for label in exported_files
        ]),
        source_labels = "".join([
            "        {},\n".format(_quote(label))
            for label in source_files
        ]),
    ))

source_package_repository = repository_rule(
    implementation = _source_package_repository_impl,
    attrs = {
        "build_script": attr.string(default = "build.ss"),
        "package": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(),
        "urls": attr.string_list(mandatory = True),
    },
)
