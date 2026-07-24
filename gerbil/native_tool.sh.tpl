#!/usr/bin/env bash
set -euo pipefail

{{ENVIRONMENT}}
toolchain_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
runfiles_repository={{RUNFILES_REPOSITORY}}
runtime_toolchain_root=$toolchain_root
executable_runfiles_root=${0}.runfiles/$runfiles_repository
if [[ -d $executable_runfiles_root ]]; then
  runtime_toolchain_root=$executable_runfiles_root
elif [[ -n ${RUNFILES_DIR:-} && -d $RUNFILES_DIR/$runfiles_repository ]]; then
  runtime_toolchain_root=$RUNFILES_DIR/$runfiles_repository
fi
absolute_tool_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$PWD" "$1" ;;
  esac
}
absolute_path_list() {
  local value=$1
  local result=
  local path
  local -a paths
  IFS=: read -r -a paths <<<"$value"
  for path in "${paths[@]}"; do
    if [[ -n $result ]]; then
      result+=:
    fi
    if [[ -z $path ]]; then
      path=.
    fi
    result+=$(absolute_tool_path "$path")
  done
  printf '%s\n' "$result"
}
if [[ -n ${GERBIL_PATH:-} ]]; then
  export GERBIL_PATH
  GERBIL_PATH=$(absolute_tool_path "$GERBIL_PATH")
fi
if [[ -n ${GERBIL_LOADPATH:-} ]]; then
  export GERBIL_LOADPATH
  GERBIL_LOADPATH=$(absolute_path_list "$GERBIL_LOADPATH")
fi
export CC
CC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-cc")
export GERBIL_GCC
GERBIL_GCC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-gcc")
export GERBIL_GSC
GERBIL_GSC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-gsc")
export GERBIL_NATIVE_ABI={{NATIVE_ABI}}
tool={{TOOL}}
tool_name={{TOOL_NAME}}
if [[ $tool_name != gxc ]]; then
  exec "$tool" "$@"
fi

set +e
"$tool" "$@"
status=$?
if (( status == 0 )); then
  exit 0
fi

hex_stream() {
  od -An -v -tx1 | tr -d '[:space:]'
}

encoding_failed=0
argv_nul_hex=
if (( $# != 0 )); then
  argv_nul_hex=$(printf '%s\0' "$@" | hex_stream) || encoding_failed=1
fi
environment_nul_hex=$(
  for name in GERBIL_HOME GERBIL_PATH GERBIL_LOADPATH GAMBOPT GERBIL_GSC GERBIL_GCC CC CFLAGS CPPFLAGS LDFLAGS SDKROOT MACOSX_DEPLOYMENT_TARGET PATH; do
    if [[ ${!name+x} == x ]]; then
      printf '%s=%s\0' "$name" "${!name}"
    fi
  done | hex_stream
) || encoding_failed=1
if (( encoding_failed != 0 )); then
  printf 'GERBIL_BAZEL_COMPILER_RECEIPT_ENCODING_FAILURE driver=GXC mode=compile-driver\n' >&2
  exit "$status"
fi
receipt_temp=
receipt_output=/dev/stderr
receipt_prefix='GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT '
input_receipt_prefix='GERBIL_BAZEL_COMPILER_INPUT_RECEIPT '
if [[ -n ${GERBIL_BAZEL_FAILURE_RECEIPT_DIR:-} ]]; then
  if mkdir -p "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR"; then
    receipt_temp=$(mktemp "$GERBIL_BAZEL_FAILURE_RECEIPT_DIR/compiler-gxc.XXXXXXXX")
    if [[ -n $receipt_temp ]]; then
      receipt_output=$receipt_temp
      receipt_prefix=
      input_receipt_prefix=
    fi
  fi
fi
receipt_write_status=0
exec 3>"$receipt_output" || receipt_write_status=$?
printf '%s{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GXC","mode":"compile-driver","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}\n' \
  "$receipt_prefix" "$status" "$argv_nul_hex" "$environment_nul_hex" >&3 || \
  receipt_write_status=$?

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
    if (( ${#digest_command[@]} != 0 )); then
      if digest=$("${digest_command[@]}" "$argument"); then
        digest=${digest%% *}
      else
        input_digest_algorithm=unavailable
        digest=
      fi
    fi
    if ! path_hex=$(printf '%s' "$argument" | hex_stream); then
      input_index=$((input_index + 1))
      continue
    fi
    printf '%s{"kind":"gerbil-bazel.compiler-input-receipt.v1","version":1,"driver":"GXC","mode":"compile-driver","index":%d,"pathHex":"%s","sizeBytes":%s,"digestAlgorithm":"%s","digest":"%s"}\n' \
      "$input_receipt_prefix" "$input_index" "$path_hex" "$size" "$input_digest_algorithm" "$digest" >&3 || \
      receipt_write_status=$?
  fi
  input_index=$((input_index + 1))
done
exec 3>&- || receipt_write_status=$?
if [[ -n $receipt_temp ]]; then
  if (( receipt_write_status == 0 )) && ln "$receipt_temp" "$receipt_temp.jsonl"; then
    rm -f "$receipt_temp"
  else
    printf 'GERBIL_BAZEL_COMPILER_FAILURE_RECEIPT {"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GXC","mode":"compile-driver","status":%d,"argvNulHex":"%s","environmentNulHex":"%s"}\n' \
      "$status" "$argv_nul_hex" "$environment_nul_hex" >&2
    printf 'GERBIL_BAZEL_COMPILER_RECEIPT_WRITE_FAILURE driver=GXC mode=compile-driver\n' >&2
    rm -f "$receipt_temp"
  fi
fi
exit "$status"
