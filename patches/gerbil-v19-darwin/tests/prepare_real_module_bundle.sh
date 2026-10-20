#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime=${1:?owned matching runtime required}
library=${2:?owned emitted library required}
manifest=${3:?tab separated C path, entry, existing alias required}
output=${4:?fresh owned fixture required}
case "$runtime:$library:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test "$(uname -s)" = Darwin
test ! -e "$output"
mkdir -p "$output/source" "$output/control" "$output/grouped"
trap 'status=$?; printf "%s\n" "$status" > "$output/prepare-exit-status.txt"' EXIT
inputs=()
seen_symbols=()
: > "$output/aliases.txt"
: > "$output/input.sha256"
while IFS=$'\t' read -r relative entry alias extra; do
  test -z "$extra"
  case "$relative" in ''|/*|../*|*/../*|*/..|./*|*/./*) exit 2 ;; *.c) ;; *) exit 2 ;; esac
  [[ "$entry" =~ ^____LNK_[[:alnum:]_]+$ ]] && [[ "$alias" =~ ^____LNK_[[:alnum:]_]+$ ]]
  test "$entry" != "$alias"
  # Default load aliases are basename-derived and can collide across directories.
  for symbol in "$entry" "$alias"; do
    for seen in "${seen_symbols[@]}"; do
      if test "$seen" = "$symbol"; then
        printf 'REAL-MODULE-BUNDLE-DENY duplicate-entry-symbol %s\n' "$symbol" >&2
        exit 2
      fi
    done
    seen_symbols+=("$symbol")
  done
  source="$library/$relative"
  object="${source%.c}.o1"
  test -f "$source" && test ! -L "$source"
  test -f "$object" && test ! -L "$object"
  symbols=$(/usr/bin/nm -gU "$object")
  entry_address=$(awk -v symbol="$entry" '$3 == symbol && $2 == "T" {print $1}' <<< "$symbols")
  alias_address=$(awk -v symbol="$alias" '$3 == symbol && $2 == "T" {print $1}' <<< "$symbols")
  [[ "$entry_address" =~ ^[[:xdigit:]]+$ ]] && test "$entry_address" = "$alias_address"
  printf '%s %s\n' "$entry" "$alias" >> "$output/aliases.txt"
  /usr/bin/shasum -a 256 "$source" "$object" >> "$output/input.sha256"
  copy="$output/source/$relative"
  mkdir -p "$(dirname "$copy")"
  cp "$source" "$copy"
  inputs+=("$copy")
  # Share untouched expansion metadata and wrapper images read-only.
  family=${relative%~*}
  for mode in control grouped; do
    mkdir -p "$output/$mode/$(dirname "$relative")"
    for path in "$library/$family".* "$library/$family"~*; do
      test -f "$path" || continue
      target="$output/$mode/${relative%/*}/$(basename "$path")"
      if test "$mode" = grouped && test "$path" = "$object"; then
        ln -s "$output/combined.o1" "$target"
      else
        ln -s "$path" "$target"
      fi
    done
  done
done < "$manifest"
test "${#inputs[@]}" -ge 2
printf -v c_inputs '%s\n' "${inputs[@]}"
sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_NATIVE_OBJECTS
env BUILD_DYN_INPUT_FILENAMES_PARAM="$c_inputs" BUILD_DYN_OUTPUT_FILENAME_PARAM="$output/combined.o1" \
  GAMBITDIR_INCLUDE="$runtime/include" GAMBITDIR_LIB="$runtime/lib" \
  BUILD_DYN_CC_OPTIONS_PARAM="-isysroot $sdk" \
  BUILD_DYN_LD_OPTIONS_PARAM="-Wl,-undefined,dynamic_lookup -Wl,-alias_list,$output/aliases.txt" \
  "$runtime/bin/gambuild-C" dyn > "$output/link.log" 2>&1
/usr/bin/nm -gU "$output/combined.o1" > "$output/combined-symbols.txt"
while read -r entry alias; do
  entry_address=$(awk -v symbol="$entry" '$3 == symbol && $2 == "T" {print $1}' "$output/combined-symbols.txt")
  alias_address=$(awk -v symbol="$alias" '$3 == symbol && $2 == "T" {print $1}' "$output/combined-symbols.txt")
  [[ "$entry_address" =~ ^[[:xdigit:]]+$ ]] && test "$entry_address" = "$alias_address"
done < "$output/aliases.txt"
/usr/bin/shasum -a 256 -c "$output/input.sha256" > "$output/input-parity.log"
printf 'REAL-MODULE-BUNDLE-PREPARED modules=%s original-C existing-entry-alias input-parity\n' "${#inputs[@]}"
