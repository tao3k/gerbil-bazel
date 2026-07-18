exports_files(["project-root.marker"])

genrule(
    name = "project_library_view_test",
    srcs = [
        "@@@REPOSITORY_NAME@@//:lib/clan/ready.txt",
        "@@@REPOSITORY_NAME@@//:lib/gslph/ready.txt",
        "@@@REPOSITORY_NAME@@//:toolchain.receipt.json",
    ],
    outs = ["project-library-view.ok"],
    cmd = "bash $(location :project_library_view_test.sh) " +
          "$(location @@@REPOSITORY_NAME@@//:toolchain.receipt.json) " +
          "$(location @@@REPOSITORY_NAME@@//:lib/clan/ready.txt) " +
          "$(location @@@REPOSITORY_NAME@@//:lib/gslph/ready.txt) $@",
    tools = [":project_library_view_test.sh"],
)
