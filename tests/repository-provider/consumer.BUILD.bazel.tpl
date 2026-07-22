exports_files(["project-root.marker"])

genrule(
    name = "project_dependency_state_missing_test",
    srcs = ["@@@REPOSITORY_NAME@@//:toolchain.receipt.json"],
    outs = ["project-dependency-state-missing.ok"],
    cmd = "bash $(location :project_dependency_state_test.sh) " +
          "$(location @@@REPOSITORY_NAME@@//:toolchain.receipt.json) " +
          "missing $@",
    tools = [":project_dependency_state_test.sh"],
)

genrule(
    name = "project_library_view_test",
    srcs = [
        "@@@REPOSITORY_NAME@@//:lib/clan/ready.txt",
        "@@@REPOSITORY_NAME@@//:lib/gslph/ready.txt",
        "@@@REPOSITORY_NAME@@//:toolchain.receipt.json",
    ],
    outs = ["project-package-manifest-view.ok"],
    cmd = "bash $(location :project_library_view_test.sh) " +
          "$(location @@@REPOSITORY_NAME@@//:toolchain.receipt.json) " +
          "$(location @@@REPOSITORY_NAME@@//:lib/clan/ready.txt) " +
          "$(location @@@REPOSITORY_NAME@@//:lib/gslph/ready.txt) $@",
    tools = [":project_library_view_test.sh"],
)
