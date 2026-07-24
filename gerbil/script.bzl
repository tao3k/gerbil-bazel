"""Compile a generated Gerbil Scheme program to a native executable."""

def _execroot_path(file):
    if file.short_path.startswith("../"):
        return "external/" + file.short_path[3:]
    return file.short_path

def _gerbil_scheme_executable_impl(ctx):
    executable = ctx.actions.declare_file(ctx.label.name)
    gxpkg = ctx.actions.declare_file(ctx.label.name + ".gxpkg")
    compile_directory = ctx.actions.declare_directory(
        ctx.label.name + ".gxc",
    )
    args = ctx.actions.args()
    args.add_all([
        "-exe",
        "-o",
        executable.path,
        "-d",
        compile_directory.path,
        ctx.file.script.path,
    ])
    ctx.actions.run(
        executable = ctx.executable.compiler,
        arguments = [args],
        env = {
            "CC": _execroot_path(ctx.file.gerbil_cc),
            "GERBIL_GCC": _execroot_path(ctx.file.gerbil_gcc),
            "GERBIL_GSC": _execroot_path(ctx.file.gerbil_gsc),
        },
        inputs = [
            ctx.file.gerbil_cc,
            ctx.file.gerbil_gcc,
            ctx.file.gerbil_gsc,
            ctx.file.script,
        ] + ctx.files.includes,
        outputs = [executable, compile_directory],
        mnemonic = "GerbilSchemeExecutable",
        progress_message = "Compiling Scheme executable %{label}",
        tools = [ctx.executable.compiler],
    )
    ctx.actions.symlink(
        output = gxpkg,
        target_file = ctx.file.gxpkg,
        is_executable = True,
    )
    return [DefaultInfo(
        executable = executable,
        runfiles = ctx.runfiles(files = [gxpkg] + ctx.files.data),
    )]

gerbil_scheme_executable = rule(
    implementation = _gerbil_scheme_executable_impl,
    attrs = {
        "compiler": attr.label(
            cfg = "exec",
            executable = True,
            mandatory = True,
        ),
        "data": attr.label_list(allow_files = True),
        "gxpkg": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "gerbil_cc": attr.label(allow_single_file = True, mandatory = True),
        "gerbil_gcc": attr.label(allow_single_file = True, mandatory = True),
        "gerbil_gsc": attr.label(allow_single_file = True, mandatory = True),
        "includes": attr.label_list(allow_files = True),
        "script": attr.label(allow_single_file = True, mandatory = True),
    },
    executable = True,
)
