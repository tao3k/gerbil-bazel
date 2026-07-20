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
set +e
"$raw_gsc" ${{gsc_options[@]+"${{gsc_options[@]}}"}} "$@"
status=$?
if (( status == 0 )); then
  exit 0
fi

hex_stream() {{
  od -An -v -tx1 | tr -d '[:space:]'
}}

encoding_failed=0
argv_nul_hex=
if (( $# != 0 )); then
  argv_nul_hex=$(printf '%s\0' "$@" | hex_stream) || encoding_failed=1
fi
environment_nul_hex=$(
  for name in GERBIL_HOME GAMBOPT GERBIL_GSC GERBIL_GCC CC CFLAGS CPPFLAGS LDFLAGS SDKROOT MACOSX_DEPLOYMENT_TARGET PATH; do
    if [[ ${{!name+x}} == x ]]; then
      printf '%s=%s\0' "$name" "${{!name}}"
    fi
  done | hex_stream
) || encoding_failed=1
if (( encoding_failed != 0 )); then
  printf 'GERBIL_BAZEL_COMPILER_RECEIPT_ENCODING_FAILURE driver=GERBIL_GSC mode=%s\n' "$mode" >&2
  exit "$status"
fi
set +e
receipt_temp=
receipt_output=/dev/stderr
failure_receipt_prefix='GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT '
input_receipt_prefix='GERBIL_BAZEL_COMPILER_INPUT_RECEIPT '
if [[ -n ${{GERBIL_BAZEL_FAILURE_RECEIPT_DIR:-}} ]]; then
  if mkdir -p "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR"; then
    receipt_temp=$(mktemp "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR/compiler-gsc.XXXXXXXX")
    if [[ -n $receipt_temp ]]; then
      receipt_output=$receipt_temp
      failure_receipt_prefix=
      input_receipt_prefix=
    fi
  fi
fi
receipt_write_failed=0
exec 3>"$receipt_output" || receipt_write_failed=1
printf '%s{{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"%s","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}}\n' \
  "$failure_receipt_prefix" "$mode" "$status" "$argv_nul_hex" "$environment_nul_hex" >&3 || receipt_write_failed=1

digest_command=()
digest_algorithm=unavailable
if command -v sha256sum >/dev/null 2>&1; then
  digest_command=(sha256sum)
  digest_algorithm=sha256
elif command -v shasum >/dev/null 2>&1; then
  digest_command=(shasum -a 256)
  digest_algorithm=sha256
fi

input_index=0
for argument in "$@"; do
  case "$argument" in
    *.c | *.scm)
      if [[ -f $argument ]]; then
        size=$(wc -c <"$argument" | tr -d '[:space:]')
        if [[ ! $size =~ ^[0-9]+$ ]]; then
          input_index=$((input_index + 1))
          continue
        fi
        digest=
        input_digest_algorithm=$digest_algorithm
        if (( ${{#digest_command[@]}} != 0 )); then
          if digest=$("${{digest_command[@]}}" "$argument"); then
            digest=${{digest%% *}}
          else
            input_digest_algorithm=unavailable
            digest=
          fi
        fi
        if ! path_hex=$(printf '%s' "$argument" | hex_stream); then
          input_index=$((input_index + 1))
          continue
        fi
        printf '%s{{"kind":"gerbil-bazel.compiler-input-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"%s","index":%d,"pathHex":"%s","sizeBytes":%s,"digestAlgorithm":"%s","digest":"%s"}}\n' \
          "$input_receipt_prefix" "$mode" "$input_index" "$path_hex" "$size" "$input_digest_algorithm" "$digest" >&3 || receipt_write_failed=1
      fi
      input_index=$((input_index + 1))
      ;;
  esac
done
exec 3>&- || receipt_write_failed=1
if [[ -n $receipt_temp ]]; then
  if (( receipt_write_failed == 0 )) && ln "$receipt_temp" "$receipt_temp.jsonl"; then
    rm -f "$receipt_temp"
  else
    printf 'GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT {{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"%s","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}}\n' \
      "$mode" "$status" "$argv_nul_hex" "$environment_nul_hex" >&2
    printf 'GERBIL_BAZEL_COMPILER_RECEIPT_WRITE_FAILURE driver=GERBIL_GSC mode=%s\n' "$mode" >&2
    rm -f "$receipt_temp"
  fi
fi
exit "$status"
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

def _materialized_executable_linker(repository_ctx, raw_linker):
    wrapper = "gerbil-gcc"
    repository_ctx.file(
        wrapper,
        """#!/usr/bin/env bash
set -euo pipefail
raw_gcc={raw_gcc}
set +e
"$raw_gcc" "$@"
status=$?
if (( status == 0 )); then
  exit 0
fi

hex_stream() {{
  od -An -v -tx1 | tr -d '[:space:]'
}}

encoding_failed=0
argv_nul_hex=
if (( $# != 0 )); then
  argv_nul_hex=$(printf '%s\0' "$@" | hex_stream) || encoding_failed=1
fi
environment_nul_hex=$(
  for name in GERBIL_HOME GAMBOPT GERBIL_GSC GERBIL_GCC CC CFLAGS CPPFLAGS LDFLAGS SDKROOT MACOSX_DEPLOYMENT_TARGET PATH; do
    if [[ ${{!name+x}} == x ]]; then
      printf '%s=%s\0' "$name" "${{!name}}"
    fi
  done | hex_stream
) || encoding_failed=1
if (( encoding_failed != 0 )); then
  printf 'GERBIL_BAZEL_COMPILER_RECEIPT_ENCODING_FAILURE driver=GERBIL_GCC mode=final-link\n' >&2
  exit "$status"
fi
set +e
receipt_temp=
receipt_output=/dev/stderr
failure_receipt_prefix='GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT '
input_receipt_prefix='GERBIL_BAZEL_COMPILER_INPUT_RECEIPT '
if [[ -n ${{GERBIL_BAZEL_FAILURE_RECEIPT_DIR:-}} ]]; then
  if mkdir -p "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR"; then
    receipt_temp=$(mktemp "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR/compiler-gcc.XXXXXXXX")
    if [[ -n $receipt_temp ]]; then
      receipt_output=$receipt_temp
      failure_receipt_prefix=
      input_receipt_prefix=
    fi
  fi
fi
receipt_write_failed=0
exec 3>"$receipt_output" || receipt_write_failed=1
printf '%s{{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GCC","mode":"final-link","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}}\n' \
  "$failure_receipt_prefix" "$status" "$argv_nul_hex" "$environment_nul_hex" >&3 || receipt_write_failed=1

digest_command=()
digest_algorithm=unavailable
if command -v sha256sum >/dev/null 2>&1; then
  digest_command=(sha256sum)
  digest_algorithm=sha256
elif command -v shasum >/dev/null 2>&1; then
  digest_command=(shasum -a 256)
  digest_algorithm=sha256
fi

input_index=0
for argument in "$@"; do
  if [[ -f $argument ]]; then
    size=$(wc -c <"$argument" | tr -d '[:space:]')
    if [[ ! $size =~ ^[0-9]+$ ]]; then
      input_index=$((input_index + 1))
      continue
    fi
    digest=
    input_digest_algorithm=$digest_algorithm
    if (( ${{#digest_command[@]}} != 0 )); then
      if digest=$("${{digest_command[@]}}" "$argument"); then
        digest=${{digest%% *}}
      else
        input_digest_algorithm=unavailable
        digest=
      fi
    fi
    if ! path_hex=$(printf '%s' "$argument" | hex_stream); then
      input_index=$((input_index + 1))
      continue
    fi
    printf '%s{{"kind":"gerbil-bazel.compiler-input-receipt.v1","version":1,"driver":"GERBIL_GCC","mode":"final-link","index":%d,"pathHex":"%s","sizeBytes":%s,"digestAlgorithm":"%s","digest":"%s"}}\n' \
      "$input_receipt_prefix" "$input_index" "$path_hex" "$size" "$input_digest_algorithm" "$digest" >&3 || receipt_write_failed=1
  fi
  input_index=$((input_index + 1))
done
exec 3>&- || receipt_write_failed=1
if [[ -n $receipt_temp ]]; then
  if (( receipt_write_failed == 0 )) && ln "$receipt_temp" "$receipt_temp.jsonl"; then
    rm -f "$receipt_temp"
  else
    printf 'GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT {{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GCC","mode":"final-link","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}}\n' \
      "$status" "$argv_nul_hex" "$environment_nul_hex" >&2
    printf 'GERBIL_BAZEL_COMPILER_RECEIPT_WRITE_FAILURE driver=GERBIL_GCC mode=final-link\n' >&2
    rm -f "$receipt_temp"
  fi
fi
exit "$status"
""".format(raw_gcc = _shell_quote(str(raw_linker))),
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
    executable_linker = gambit_executable_linker if gambit_executable_linker else str(compiler.path)
    gcc = _materialized_executable_linker(repository_ctx, executable_linker)
    output = dict(environment)
    gambopt = output.get("GAMBOPT", repository_ctx.os.environ.get("GAMBOPT", ""))
    gambopt = _append_runtime_option(gambopt, "~~={}".format(gerbil_home))
    gambopt = _append_runtime_option(gambopt, "~~bin={}".format(gambit_bin))
    gambopt = _append_runtime_option(gambopt, "~~lib={}".format(gambit_lib))
    output.update({
        "CC": str(compiler.path),
        "GAMBOPT": gambopt,
        "GERBIL_GCC": str(gcc),
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
        gcc_path = gcc,
        gsc_path = gsc,
        producer_dynamic_options = producer_options.dynamic,
        producer_object_options = producer_options.object,
    )
