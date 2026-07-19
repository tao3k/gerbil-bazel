"""Shared Gambit runtime normalization for Gerbil toolchain repositories."""

def _append_runtime_option(options, option):
    if not options:
        return option
    if options.endswith(","):
        return options + option
    return options + "," + option

def _normalized_gambuild_compiler(source, dynamic_link_options):
    normalized_guard = "if test \"${GERBIL_GCC+set}\" = set; then"
    normalized_binding = "  C_COMPILER=\"${GERBIL_GCC}\""
    if normalized_guard in source:
        if normalized_binding not in source:
            fail("Gambit gambuild-C has an invalid GERBIL_GCC normalization guard")
        compiler_source = source
    else:
        output = []
        replacements = 0
        for line in source.split("\n"):
            if line.startswith("C_COMPILER="):
                output.extend([
                    "if test \"${GERBIL_GCC+set}\" = set; then",
                    "  C_COMPILER=\"${GERBIL_GCC}\"",
                    "else",
                    "  {}".format(line),
                    "fi",
                ])
                replacements += 1
            else:
                output.append(line)
        if replacements != 1:
            fail("Gambit gambuild-C must contain exactly one C_COMPILER binding; got {}".format(
                replacements,
            ))
        compiler_source = "\n".join(output)

    if not dynamic_link_options:
        return compiler_source

    dynamic_binding = 'FLAGS_DYN="${{FLAGS_DYN}} {}"'.format(dynamic_link_options)
    if dynamic_binding in compiler_source:
        return compiler_source
    output = []
    replacements = 0
    for line in compiler_source.split("\n"):
        output.append(line)
        if line.startswith("FLAGS_DYN="):
            output.append(dynamic_binding)
            replacements += 1
    if replacements != 1:
        fail("Gambit gambuild-C must contain exactly one FLAGS_DYN binding; got {}".format(
            replacements,
        ))
    return "\n".join(output)

def _normalized_gambit_bin(repository_ctx, gambit_bin, dynamic_link_options):
    gambuild = repository_ctx.path("{}/gambuild-C".format(gambit_bin))
    if not gambuild.exists:
        return gambit_bin

    overlay = "gambit-bin"
    repository_ctx.file("{}/.root".format(overlay), "gerbil-bazel Gambit bin overlay\n")
    for entry in gambit_bin.readdir():
        if entry.basename != "gambuild-C":
            repository_ctx.symlink(entry, "{}/{}".format(overlay, entry.basename))
    repository_ctx.file(
        "{}/gambuild-C".format(overlay),
        _normalized_gambuild_compiler(
            repository_ctx.read(gambuild),
            dynamic_link_options,
        ),
        executable = True,
    )
    return repository_ctx.path(overlay)

def discover_gambit_home(repository_ctx, gxi):
    """Returns the native Gambit home reported by the selected Gerbil runtime."""
    result = repository_ctx.execute(
        [
            gxi,
            "-e",
            "(begin (display (path-expand \"~~\")) (newline))",
        ],
        quiet = True,
    )
    if result.return_code != 0:
        fail("Gambit home discovery failed: {}".format(result.stderr.strip()))
    home = result.stdout.strip()
    if not home or not home.startswith("/"):
        fail("Gambit home must be an absolute path; got {!r}".format(home))
    return home.rstrip("/")

def discover_gambit_compiler_command(repository_ctx, gerbil_home):
    """Returns the literal producer compiler command declared by Gambit."""
    gambuild = repository_ctx.path("{}/bin/gambuild-C".format(gerbil_home))
    if not gambuild.exists:
        fail("Gambit compiler driver does not exist: {}".format(gambuild))

    compilers = []
    for line in repository_ctx.read(gambuild).split("\n"):
        if not line.startswith("C_COMPILER="):
            continue
        value = line[len("C_COMPILER="):].strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        if value and "$" not in value:
            compilers.append(value)
    if len(compilers) != 1:
        fail("Gambit gambuild-C must declare exactly one literal producer compiler; got {}".format(
            len(compilers),
        ))

    return compilers[0]

def _materialized_compiler(repository_ctx, compiler_command):
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./:+-=, "
    for character in compiler_command.elems():
        if character not in allowed:
            fail("Gambit producer compiler command contains an unsafe character: {!r}".format(
                character,
            ))

    wrapper = "gerbil-cc"
    repository_ctx.file(
        wrapper,
        "#!/usr/bin/env bash\nset -euo pipefail\nexec {} \"$@\"\n".format(
            compiler_command,
        ),
        executable = True,
    )
    wrapper_path = repository_ctx.path(wrapper)
    identity_result = repository_ctx.execute(
        [str(wrapper_path), "--version"],
        quiet = True,
    )
    if identity_result.return_code != 0:
        fail("Gambit producer compiler identity probe failed for {!r}: {}".format(
            compiler_command,
            identity_result.stderr.strip(),
        ))
    identity = "gerbil-cc.identity.txt"
    repository_ctx.file(
        identity,
        "command={}\n{}\n{}\n".format(
            compiler_command,
            identity_result.stdout.strip(),
            identity_result.stderr.strip(),
        ),
    )
    return struct(
        command = compiler_command,
        identity_path = repository_ctx.path(identity),
        path = wrapper_path,
    )

def normalized_gambit_runtime(
        repository_ctx,
        gerbil_home,
        compiler_command,
        environment,
        gambit_dynamic_link_options = ""):
    """Returns an environment that consumes a compiler-only gambuild-C overlay."""
    gambit_bin = repository_ctx.path("{}/bin".format(gerbil_home))
    gambit_lib = repository_ctx.path("{}/lib".format(gerbil_home))
    if not gambit_bin.exists or not gambit_lib.exists:
        fail("Gerbil home must contain Gambit bin and lib directories: {}".format(
            gerbil_home,
        ))
    gerbil_gsc = repository_ctx.path("{}/gsc".format(gambit_bin))
    if not gerbil_gsc.exists:
        fail("Gerbil compiler driver does not exist: {}".format(gerbil_gsc))

    compiler = _materialized_compiler(repository_ctx, compiler_command)
    runtime_bin = _normalized_gambit_bin(
        repository_ctx,
        gambit_bin,
        gambit_dynamic_link_options,
    )
    output = dict(environment)
    gambopt = output.get("GAMBOPT", repository_ctx.os.environ.get("GAMBOPT", ""))
    gambopt = _append_runtime_option(gambopt, "~~={}".format(gerbil_home))
    gambopt = _append_runtime_option(gambopt, "~~bin={}".format(runtime_bin))
    gambopt = _append_runtime_option(gambopt, "~~lib={}".format(gambit_lib))
    output.update({
        "CC": str(compiler.path),
        "GAMBOPT": gambopt,
        "GERBIL_GCC": str(compiler.path),
        "GERBIL_GSC": str(gerbil_gsc),
        "GERBIL_HOME": gerbil_home,
    })
    return struct(
        compiler_command = compiler.command,
        compiler_identity_path = compiler.identity_path,
        compiler_path = compiler.path,
        environment = output,
    )
