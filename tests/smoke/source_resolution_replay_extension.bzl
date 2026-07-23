load(
    "//gerbil:project_dependency_sources_repository.bzl",
    "project_dependency_sources_repository",
)

_CANONICAL_PACKAGE_PATH = ".gerbil/pkg/clan"
_CANONICAL_URI = "https://example.invalid/gerbil-bazel-source-resolution-fixture"
_EXPECTED_REVISION = "eaf43dc92bfeeb9abeb348137a7cca449843936f"

def _source_resolution_fixture_repository_impl(repository_ctx):
    repository_ctx.file(
        "BUILD.bazel",
        """exports_files(
    ["project-root.marker"],
    visibility = ["//visibility:public"],
)
""",
    )
    repository_ctx.file(
        "project-root.marker",
        "gerbil-bazel source-resolution replay fixture\n",
    )
    repository_ctx.file(
        ".gerbil/pkg/clan/ready.txt",
        "ready\n",
    )

    environment = {
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
    }
    commands = [
        ["git", "init", "-q"],
        [
            "git",
            "-c",
            "user.name=gerbil-bazel fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "add",
            ".",
        ],
        [
            "git",
            "-c",
            "user.name=gerbil-bazel fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-q",
            "-m",
            "source-resolution replay fixture",
        ],
        ["git", "remote", "add", "origin", _CANONICAL_URI + ".git"],
    ]
    for command in commands:
        result = repository_ctx.execute(command, environment = environment, quiet = True)
        if result.return_code != 0:
            fail("failed to create source-resolution replay fixture: {}".format(
                result.stderr,
            ))

source_resolution_fixture_repository = repository_rule(
    implementation = _source_resolution_fixture_repository_impl,
)

def _source_resolution_replay_impl(_module_ctx):
    source_resolution_fixture_repository(
        name = "source_resolution_replay_fixture",
    )
    common = {
        "package": "gerbil-bazel-self",
        "project_root_marker": Label("@@+source_resolution_replay+source_resolution_replay_fixture//:project-root.marker"),
        "project_library_relative_path": "project-library",
        "canonical_package_path": _CANONICAL_PACKAGE_PATH,
        "canonical_uri": _CANONICAL_URI,
        "expected_revision": _EXPECTED_REVISION,
    }
    project_dependency_sources_repository(
        name = "source_resolution_replay_a",
        **common
    )
    project_dependency_sources_repository(
        name = "source_resolution_replay_b",
        **common
    )

source_resolution_replay = module_extension(
    implementation = _source_resolution_replay_impl,
)
