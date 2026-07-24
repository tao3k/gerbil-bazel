"""Public AOT object and native link-plan capabilities for Gerbil packages."""

load(
    ":providers.bzl",
    "GerbilAotObjectInfo",
    "GerbilNativeLinkPlanInfo",
    "GerbilPackageInfo",
)
load(":toolchain.bzl", "GERBIL_TOOLCHAIN_TYPE", "resolved_gerbil_toolchain")

_MODULE_CHARACTERS = (
    "abcdefghijklmnopqrstuvwxyz" +
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
    "0123456789._+-/"
)
_C_IDENTIFIER_CHARACTERS = (
    "abcdefghijklmnopqrstuvwxyz" +
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
    "0123456789_"
)

def _validate_module(module):
    if not module or module.startswith("/") or module.endswith("/"):
        fail("Gerbil AOT module must be a non-empty canonical module identifier")
    for segment in module.split("/"):
        if segment in ["", ".", ".."]:
            fail("Gerbil AOT module contains an unsafe path segment: {}".format(module))
    for character in module.elems():
        if character not in _MODULE_CHARACTERS:
            fail("Gerbil AOT module contains an unsupported character: {!r}".format(
                character,
            ))

def _validate_c_identifier(value, description):
    if not value:
        fail("{} must not be empty".format(description))
    if value[0] in "0123456789":
        fail("{} must not begin with a digit: {}".format(description, value))
    for character in value.elems():
        if character not in _C_IDENTIFIER_CHARACTERS:
            fail("{} must be a C identifier, got {!r}".format(description, value))

def _static_module_path(package_root, module):
    return "{}/.gerbil/lib/static/{}.scm".format(
        package_root.path,
        module.replace("/", "__"),
    )

def _compile_expression(module, staged_scm, generated_c):
    return "(compile-file-to-target {} output: {} module-name: {})".format(
        json.encode(staged_scm.path),
        json.encode(generated_c.path),
        json.encode(module),
    )

def _command(operation, argv):
    return {
        "argv": argv,
        "operation": operation,
    }

def _extra_object(ctx, index, source):
    basename = source.basename
    if basename.endswith(".c"):
        basename = basename[:-2]
    return ctx.actions.declare_file(
        "{}.aot/native-{}-{}.o".format(ctx.label.name, index, basename),
    )

def _gerbil_aot_objects_impl(ctx):
    _validate_module(ctx.attr.module)
    _validate_c_identifier(ctx.attr.linker_name, "linker_name")
    _validate_c_identifier(ctx.attr.main_symbol, "main_symbol")

    package = ctx.attr.package[GerbilPackageInfo]
    toolchain = resolved_gerbil_toolchain(ctx)
    if not toolchain.gambit_static_link_available:
        fail((
            "{} requires a Gerbil toolchain capability that publishes " +
            "libgambit.a"
        ).format(ctx.label))
    module_leaf = ctx.attr.module.split("/")[-1]
    staged_scm = ctx.actions.declare_file(
        "{}.aot/{}.scm".format(ctx.label.name, module_leaf),
    )
    module_c = ctx.actions.declare_file(
        "{}.aot/{}.c".format(ctx.label.name, module_leaf),
    )
    module_object = ctx.actions.declare_file(
        "{}.aot/{}.o".format(ctx.label.name, module_leaf),
    )
    linker_c = ctx.actions.declare_file(
        "{}.aot/{}_link.c".format(ctx.label.name, module_leaf),
    )
    linker_object = ctx.actions.declare_file(
        "{}.aot/{}_link.o".format(ctx.label.name, module_leaf),
    )
    extra_objects = [
        _extra_object(ctx, index, source)
        for index, source in enumerate(ctx.files.c_srcs)
    ]
    request = ctx.actions.declare_file(ctx.label.name + ".aot.request.json")
    plan = ctx.actions.declare_file(ctx.label.name + ".native-link-plan.json")
    receipt = ctx.actions.declare_file(ctx.label.name + ".aot.receipt.json")
    log = ctx.actions.declare_file(ctx.label.name + ".aot.log")

    commands = [
        _command(
            "generate Gambit linker C",
            [
                toolchain.gerbil_gsc.path,
                "-link",
                "-linker-name",
                ctx.attr.linker_name,
                "-o",
                linker_c.path,
                staged_scm.path,
            ],
        ),
        _command(
            "generate named Gerbil module C",
            [
                toolchain.gerbil_gsc.path,
                "-e",
                _compile_expression(ctx.attr.module, staged_scm, module_c),
            ],
        ),
        _command(
            "compile Gerbil module object",
            [
                toolchain.gerbil_gsc.path,
                "-obj",
                "-o",
                module_object.path,
                module_c.path,
            ],
        ),
        _command(
            "compile Gambit linker object",
            [
                toolchain.gerbil_gsc.path,
                "-obj",
                "-cc-options",
                "-Dmain={}".format(ctx.attr.main_symbol),
                "-o",
                linker_object.path,
                linker_c.path,
            ],
        ),
    ]
    for index in range(len(ctx.files.c_srcs)):
        commands.append(_command(
            "compile explicit native source {}".format(ctx.files.c_srcs[index].basename),
            [
                toolchain.gerbil_gsc.path,
                "-obj",
                "-o",
                extra_objects[index].path,
                ctx.files.c_srcs[index].path,
            ],
        ))

    compile_outputs = [
        staged_scm,
        module_c,
        module_object,
        linker_c,
        linker_object,
    ] + extra_objects
    ctx.actions.write(
        output = request,
        content = json.encode({
            "commands": commands,
            "copies": [{
                "destination": staged_scm.path,
                "source": _static_module_path(package.package_root, ctx.attr.module),
            }],
            "log": log.path,
            "outputs": [output.path for output in compile_outputs],
            "schema": "gerbil-bazel.aot-request.v1",
            "workingDirectory": ".",
        }) + "\n",
    )

    dependency_roots = package.dependency_roots.to_list()
    environment = dict(toolchain.environment)
    environment.update({
        "GERBIL_BAZEL_NATIVE_ABI": toolchain.native_abi_fingerprint,
        "GERBIL_LOADPATH": ":".join(
            [package.package_root.path + "/.gerbil/lib"] +
            [
                dependency.path + "/.gerbil/lib"
                for dependency in dependency_roots
            ] +
            [toolchain.dependency_library_root.dirname],
        ),
        "GERBIL_PATH": package.package_root.path + "/.gerbil",
    })
    ctx.actions.run(
        arguments = [ctx.file._runner.path, request.path],
        env = environment,
        executable = toolchain.gxi,
        inputs = depset(
            direct = [
                ctx.file._functional,
                ctx.file._runner,
                package.package_root,
                request,
                toolchain.dependency_library_root,
                toolchain.gambit_library_root,
                toolchain.gerbil_gsc,
                toolchain.native_abi_fingerprint_file,
            ] + ctx.files.c_srcs,
            transitive = [
                package.dependency_roots,
                toolchain.compile_runfiles,
                toolchain.gambit_libraries,
            ],
        ),
        mnemonic = "GerbilAotObjects",
        outputs = compile_outputs + [log],
        progress_message = "Compiling Gerbil AOT objects %{label}",
        tools = [toolchain.gxi],
    )

    module_objects = depset(
        direct = [module_object] + extra_objects,
        order = "postorder",
    )
    link_search_directory = toolchain.gambit_library_root.dirname + "/lib"
    ctx.actions.write(
        output = plan,
        content = json.encode_indent({
            "linkLibraries": toolchain.gambit_link_libraries,
            "linkObject": linker_object.path,
            "linkSearchDirectories": [link_search_directory],
            "moduleObjects": [
                output.path
                for output in module_objects.to_list()
            ],
            "schema": "gerbil-bazel.native-link-plan.v1",
        }, indent = "  ") + "\n",
    )
    ctx.actions.write(
        output = receipt,
        content = json.encode_indent({
            "explicitNativeSourceLabels": [
                str(source.owner)
                for source in ctx.files.c_srcs
            ],
            "linkLibraries": toolchain.gambit_link_libraries,
            "linkerName": ctx.attr.linker_name,
            "mainSymbol": ctx.attr.main_symbol,
            "module": ctx.attr.module,
            "nativeAbiFingerprint": toolchain.native_abi_fingerprint,
            "packageIdentity": package.package_identity,
            "packageReference": package.package_reference,
            "schema": "gerbil-bazel.aot-receipt.v1",
        }, indent = "  ") + "\n",
    )

    object_info = GerbilAotObjectInfo(
        generated_c = depset([module_c, linker_c]),
        link_object = linker_object,
        log = log,
        module = ctx.attr.module,
        module_objects = module_objects,
        receipt = receipt,
    )
    link_plan_info = GerbilNativeLinkPlanInfo(
        link_inputs = toolchain.gambit_libraries,
        link_libraries = toolchain.gambit_link_libraries,
        link_object = linker_object,
        link_search_roots = depset([toolchain.gambit_library_root]),
        module_objects = module_objects,
        plan = plan,
        receipt = receipt,
    )
    return [
        DefaultInfo(files = depset(compile_outputs + [log, plan, receipt])),
        object_info,
        link_plan_info,
        OutputGroupInfo(
            generated_c = depset([module_c, linker_c]),
            link_plan = depset([plan]),
            log = depset([log]),
            native_objects = depset([module_object, linker_object] + extra_objects),
            receipt = depset([receipt]),
            staged_scm = depset([staged_scm]),
        ),
    ]

gerbil_aot_objects = rule(
    implementation = _gerbil_aot_objects_impl,
    attrs = {
        "c_srcs": attr.label_list(allow_files = [".c"]),
        "linker_name": attr.string(mandatory = True),
        "main_symbol": attr.string(mandatory = True),
        "module": attr.string(mandatory = True),
        "package": attr.label(mandatory = True, providers = [GerbilPackageInfo]),
        "_functional": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:functional.ss",
        ),
        "_runner": attr.label(
            allow_single_file = True,
            default = "@gerbil_bazel//gerbil:aot_runner.ss",
        ),
    },
    doc = "Compiles one explicit module from a GerbilPackageInfo into native objects.",
    toolchains = [GERBIL_TOOLCHAIN_TYPE],
)
