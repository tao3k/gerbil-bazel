"""Shared Gambit runtime normalization for Gerbil toolchain repositories."""

def _append_runtime_option(options, option):
    if not options:
        return option
    if options.endswith(","):
        return options + option
    return options + "," + option

def _shell_quote(value):
    return "'{}'".format(value.replace("'", "'\"'\"'"))

def _gambuild_value(repository_ctx, gerbil_home, variable):
    gambuild = repository_ctx.path("{}/bin/gambuild-C".format(gerbil_home))
    if not gambuild.exists:
        fail("Gambit compiler driver does not exist: {}".format(gambuild))
    result = repository_ctx.execute([str(gambuild), variable], quiet = True)
    if result.return_code != 0:
        fail("Gambit {} discovery failed: {}".format(
            variable,
            result.stderr.strip(),
        ))
    return result.stdout.strip()

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

def discover_gambit_producer_options(repository_ctx, gerbil_home):
    """Returns the installed producer flags cleared by Gambit's -cc override."""
    return struct(
        dynamic = _gambuild_value(repository_ctx, gerbil_home, "FLAGS_DYN"),
        object = _gambuild_value(repository_ctx, gerbil_home, "FLAGS_OBJ"),
    )

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
        producer_options,
        dynamic_link_options):
    wrapper = "gerbil-gsc"
    repository_ctx.file(
        wrapper,
        """#!/usr/bin/env bash
set -euo pipefail
raw_gsc={raw_gsc}
producer_compiler={producer_compiler}
producer_object_options={producer_object_options}
producer_dynamic_options={producer_dynamic_options}
platform_dynamic_link_options={platform_dynamic_link_options}
mode=dynamic
for argument in "$@"; do
  case "$argument" in
    -c | -link | -obj | -exe | -dynamic) mode=${{argument#-}} ;;
  esac
done
gsc_options=()
case "$mode" in
  obj)
    gsc_options+=(-cc "$producer_compiler")
    if [[ -n $producer_object_options ]]; then
      gsc_options+=(-cc-options "$producer_object_options")
    fi
    ;;
  dynamic)
    gsc_options+=(-cc "$producer_compiler")
    dynamic_options=$producer_dynamic_options
    if [[ -n $platform_dynamic_link_options ]]; then
      if [[ -n $dynamic_options ]]; then
        dynamic_options+=" "
      fi
      dynamic_options+=$platform_dynamic_link_options
    fi
    if [[ -n $dynamic_options ]]; then
      gsc_options+=(-ld-options "$dynamic_options")
    fi
    ;;
esac
exec "$raw_gsc" "${{gsc_options[@]}}" "$@"
""".format(
            platform_dynamic_link_options = _shell_quote(dynamic_link_options),
            producer_compiler = _shell_quote(str(producer_compiler)),
            producer_dynamic_options = _shell_quote(producer_options.dynamic),
            producer_object_options = _shell_quote(producer_options.object),
            raw_gsc = _shell_quote(str(raw_gsc)),
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
    producer_options = discover_gambit_producer_options(repository_ctx, gerbil_home)
    gsc = _materialized_gsc(
        repository_ctx,
        gerbil_gsc,
        compiler.path,
        producer_options,
        gambit_dynamic_link_options,
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
        producer_dynamic_options = producer_options.dynamic,
        producer_object_options = producer_options.object,
    )
