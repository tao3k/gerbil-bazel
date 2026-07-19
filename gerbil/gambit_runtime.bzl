"""Shared Gambit runtime normalization for Gerbil toolchain repositories."""

def _append_runtime_option(options, option):
    if not options:
        return option
    if options.endswith(","):
        return options + option
    return options + "," + option

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

def _materialized_gsc(
        repository_ctx,
        raw_gsc,
        producer_compiler,
        dynamic_link_options,
        executable_linker):
    wrapper = "gerbil-gsc"
    repository_ctx.file(
        wrapper,
        """#!/usr/bin/env bash
set -euo pipefail
raw_gsc={raw_gsc}
producer_compiler={producer_compiler}
dynamic_link_options={dynamic_link_options}
executable_linker={executable_linker}
mode=dynamic
for argument in "$@"; do
  case "$argument" in
    -c | -link | -obj | -exe | -dynamic) mode=${{argument#-}} ;;
  esac
done
compiler=$producer_compiler
if [[ $mode == exe && -n $executable_linker ]]; then
  compiler=$executable_linker
fi
gsc_options=(-cc "$compiler")
if [[ $mode == dynamic && -n $dynamic_link_options ]]; then
  gsc_options+=(-ld-options "$dynamic_link_options")
fi
exec "$raw_gsc" "${{gsc_options[@]}}" "$@"
""".format(
            dynamic_link_options = repr(dynamic_link_options),
            executable_linker = repr(executable_linker),
            producer_compiler = repr(str(producer_compiler)),
            raw_gsc = repr(str(raw_gsc)),
        ),
        executable = True,
    )
    return repository_ctx.path(wrapper)

def normalized_gambit_runtime(
        repository_ctx,
        gerbil_home,
        compiler_command,
        environment,
        gambit_dynamic_link_options = "",
        gambit_executable_linker = ""):
    """Returns an environment using upstream Gerbil and Gambit compiler hooks."""
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
    gsc = _materialized_gsc(
        repository_ctx,
        gerbil_gsc,
        compiler.path,
        gambit_dynamic_link_options,
        gambit_executable_linker,
    )
    output = dict(environment)
    gambopt = output.get("GAMBOPT", repository_ctx.os.environ.get("GAMBOPT", ""))
    gambopt = _append_runtime_option(gambopt, "~~={}".format(gerbil_home))
    gambopt = _append_runtime_option(gambopt, "~~bin={}".format(gambit_bin))
    gambopt = _append_runtime_option(gambopt, "~~lib={}".format(gambit_lib))
    output.update({
        "CC": str(compiler.path),
        "GAMBOPT": gambopt,
        "GERBIL_GCC": gambit_executable_linker if gambit_executable_linker else str(compiler.path),
        "GERBIL_GSC": str(gsc),
        "GERBIL_HOME": gerbil_home,
    })
    if gambit_executable_linker:
        output["GERBIL_BAZEL_EXE_LINKER"] = gambit_executable_linker
    return struct(
        compiler_command = compiler.command,
        compiler_identity_path = compiler.identity_path,
        compiler_path = compiler.path,
        environment = output,
        executable_linker = gambit_executable_linker,
        gsc_path = gsc,
    )
