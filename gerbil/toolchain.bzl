"""Gerbil toolchain provider and registration rule."""

GERBIL_TOOLCHAIN_TYPE = "@gerbil_bazel//gerbil:toolchain_type"

GerbilToolchainInfo = provider(
    doc = "Resolved Gerbil executables and host capabilities.",
    fields = {
        "dependency_libraries": "depset of configured Gerbil dependency files",
        "dependency_library_root": "root marker for the configured libraries",
        "environment": "normalized environment inherited by Gerbil actions",
        "gerbil_as": "assembler executable",
        "gerbil_cc": "C compiler executable path",
        "gerbil_ld": "linker executable",
        "gxc": "Gerbil compiler FilesToRunProvider",
        "gxi": "Gerbil interpreter FilesToRunProvider",
        "gxpkg": "Gerbil package tool FilesToRunProvider",
        "gxtest": "Gerbil test runner FilesToRunProvider",
        "native_abi_fingerprint": "host-native ABI fingerprint",
        "native_abi_fingerprint_file": "file containing the ABI fingerprint",
        "native_scheme_env": "environment runner FilesToRunProvider",
        "receipt": "toolchain discovery receipt",
        "runfiles": "all files required to execute the toolchain",
        "system_cpu_count": "available logical CPUs discovered from the host",
        "system_memory_bytes": "available physical memory discovered from the host",
    },
)

def resolved_gerbil_toolchain(ctx):
    """Returns GerbilToolchainInfo from a rule that declares the toolchain."""
    return ctx.toolchains[GERBIL_TOOLCHAIN_TYPE].gerbil

def _files_to_run(target):
    return target[DefaultInfo].files_to_run

def _gerbil_toolchain_impl(ctx):
    tools = [ctx.attr.gxc, ctx.attr.gxi, ctx.attr.gxpkg, ctx.attr.gxtest]
    direct_files = [
        ctx.file.dependency_library_root,
        ctx.file.gerbil_cc,
        ctx.file.native_abi_fingerprint_file,
        ctx.file.receipt,
        ctx.attr.native_scheme_env[DefaultInfo].files_to_run.executable,
    ]
    transitive = [
        ctx.attr.dependency_libraries[DefaultInfo].files,
        ctx.attr.native_scheme_env[DefaultInfo].default_runfiles.files,
    ]
    for target in tools:
        direct_files.append(target[DefaultInfo].files_to_run.executable)
        transitive.append(target[DefaultInfo].default_runfiles.files)

    info = GerbilToolchainInfo(
        dependency_libraries = ctx.attr.dependency_libraries[DefaultInfo].files,
        dependency_library_root = ctx.file.dependency_library_root,
        environment = dict(ctx.attr.environment),
        gerbil_as = ctx.attr.gerbil_as,
        gerbil_cc = ctx.file.gerbil_cc.path,
        gerbil_ld = ctx.attr.gerbil_ld,
        gxc = _files_to_run(ctx.attr.gxc),
        gxi = _files_to_run(ctx.attr.gxi),
        gxpkg = _files_to_run(ctx.attr.gxpkg),
        gxtest = _files_to_run(ctx.attr.gxtest),
        native_abi_fingerprint = ctx.attr.native_abi_fingerprint,
        native_abi_fingerprint_file = ctx.file.native_abi_fingerprint_file,
        native_scheme_env = _files_to_run(ctx.attr.native_scheme_env),
        receipt = ctx.file.receipt,
        runfiles = depset(direct = direct_files, transitive = transitive),
        system_cpu_count = ctx.attr.system_cpu_count,
        system_memory_bytes = ctx.attr.system_memory_bytes,
    )
    return [platform_common.ToolchainInfo(gerbil = info)]

gerbil_toolchain = rule(
    implementation = _gerbil_toolchain_impl,
    attrs = {
        "dependency_libraries": attr.label(mandatory = True),
        "dependency_library_root": attr.label(allow_single_file = True, mandatory = True),
        "environment": attr.string_dict(),
        "gerbil_as": attr.string(mandatory = True),
        "gerbil_cc": attr.label(allow_single_file = True, mandatory = True),
        "gerbil_ld": attr.string(mandatory = True),
        "gxc": attr.label(cfg = "exec", executable = True, mandatory = True),
        "gxi": attr.label(cfg = "exec", executable = True, mandatory = True),
        "gxpkg": attr.label(cfg = "exec", executable = True, mandatory = True),
        "gxtest": attr.label(cfg = "exec", executable = True, mandatory = True),
        "native_abi_fingerprint": attr.string(mandatory = True),
        "native_abi_fingerprint_file": attr.label(allow_single_file = True, mandatory = True),
        "native_scheme_env": attr.label(cfg = "exec", executable = True, mandatory = True),
        "receipt": attr.label(allow_single_file = True, mandatory = True),
        "system_cpu_count": attr.string(mandatory = True),
        "system_memory_bytes": attr.string(mandatory = True),
    },
)
