#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_CAPABILITY_ARCHIVE:?GERBIL_CAPABILITY_ARCHIVE is required}"
: "${GERBIL_PREFIX:?GERBIL_PREFIX is required}"
: "${GERBIL_REF:?GERBIL_REF is required}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
prefix="$(cd "$GERBIL_PREFIX" && pwd)"
archive_dir="$(dirname "$GERBIL_CAPABILITY_ARCHIVE")"
mkdir -p "$archive_dir"
archive="$(cd "$archive_dir" && pwd)/$(basename "$GERBIL_CAPABILITY_ARCHIVE")"
output_stem="${archive%.tar.gz}"
stage="$(mktemp -d)"
relocation_root="$(mktemp -d)"
started_at="$SECONDS"

cleanup() {
  rm -rf "$stage" "$relocation_root"
}
trap cleanup EXIT

normalize_arch() {
  case "$1" in
    amd64 | x86_64) printf 'x86_64\n' ;;
    aarch64 | arm64) printf 'aarch64\n' ;;
    *)
      printf 'unsupported capability architecture: %s\n' "$1" >&2
      return 64
      ;;
  esac
}

system="$(uname -s | tr '[:upper:]' '[:lower:]')"
if [[ "$system" != linux ]]; then
  printf 'prebuilt capability production is currently Linux-only; got %s\n' "$system" >&2
  exit 64
fi
architecture="$(normalize_arch "$(uname -m)")"

mkdir -p "$stage/prefix"
cp -a "$prefix/." "$stage/prefix/"

while IFS= read -r -d '' link; do
  target="$(readlink "$link")"
  if [[ "$target" == /* ]]; then
    printf 'capability contains a non-relocatable absolute symlink: %s -> %s\n' \
      "${link#"$stage/"}" "$target" >&2
    exit 65
  fi
done < <(find "$stage/prefix" -type l -print0)

declare -A tool_sources
tools='{}'
for name in gxc gxi gxpkg gxtest; do
  source_path="$prefix/bin/$name"
  if [[ ! -e "$source_path" ]]; then
    source_path="$prefix/current/bin/$name"
  fi
  if [[ ! -e "$source_path" ]]; then
    printf 'Gerbil capability tool is missing: %s\n' "$name" >&2
    exit 66
  fi
  tool_sources["$name"]="$source_path"
  relative="prefix/${source_path#"$prefix/"}"
  tools="$(jq -c --arg name "$name" --arg relative "$relative" \
    '. + {($name): $relative}' <<<"$tools")"
done

if [[ -d "$prefix/current" ]]; then
  gerbil_home=prefix/current
else
  gerbil_home=prefix
fi

dependency_roots='[]'
for candidate in "$prefix/lib" "$prefix/current/lib"; do
  if [[ -d "$candidate" ]]; then
    relative="prefix/${candidate#"$prefix/"}"
    dependency_roots="$(jq -c --arg relative "$relative" \
      '. + [$relative] | unique' <<<"$dependency_roots")"
  fi
done
if [[ "$(jq 'length' <<<"$dependency_roots")" -eq 0 ]]; then
  printf 'Gerbil capability has no dependency library root\n' >&2
  exit 67
fi

cc="$(command -v "${CC:-cc}")"
assembler="$(command -v "${AS:-as}")"
linker="$(command -v "${LD:-ld}")"
native_abi="$({
  "$repo_root/gerbil/native_abi_fingerprint.sh" \
    "${tool_sources[gxi]}" \
    "${tool_sources[gxc]}" \
    "${tool_sources[gxpkg]}" \
    "${tool_sources[gxtest]}" \
    "$cc" \
    "$assembler" \
    "$linker"
} | tr -d '\n')"
if [[ ! "$native_abi" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'native ABI probe did not produce a SHA-1 fingerprint: %s\n' "$native_abi" >&2
  exit 68
fi

version="$("${tool_sources[gxi]}" --version)"
capability_id="gerbil-${GERBIL_REF}-${system}-${architecture}"
manifest="$stage/gerbil-bazel-capability.json"
jq -n \
  --arg schema gerbil-bazel.prebuilt-capability-manifest.v1 \
  --arg capability_id "$capability_id" \
  --arg version "$version" \
  --arg native_abi "$native_abi" \
  --arg system "$system" \
  --arg architecture "$architecture" \
  --arg gerbil_home "$gerbil_home" \
  --argjson tools "$tools" \
  --argjson dependency_roots "$dependency_roots" \
  '{
    schema: $schema,
    capabilityId: $capability_id,
    version: $version,
    nativeAbiFingerprint: $native_abi,
    platform: {os: $system, arch: $architecture},
    gerbilHome: $gerbil_home,
    tools: $tools,
    dependencyRoots: $dependency_roots,
    environment: {}
  }' >"$manifest"

archive_started_at="$SECONDS"
tar \
  --sort=name \
  --mtime='UTC 1970-01-01' \
  --owner=0 \
  --group=0 \
  --numeric-owner \
  -C "$stage" \
  -czf "$archive" \
  .
archive_seconds="$((SECONDS - archive_started_at))"

archive_sha256="$(sha256sum "$archive" | awk '{print $1}')"
archive_size_bytes="$(stat -c '%s' "$archive")"
printf '%s  %s\n' "$archive_sha256" "$(basename "$archive")" >"$output_stem.sha256"
cp "$manifest" "$output_stem.manifest.json"

relocation_started_at="$SECONDS"
tar -xzf "$archive" -C "$relocation_root"
relocated_home="$relocation_root/$gerbil_home"
relocated_gsc="$relocated_home/bin/gsc"
relocated_gxc="$relocation_root/$(jq -r '.gxc' <<<"$tools")"
relocated_gxi="$relocation_root/$(jq -r '.gxi' <<<"$tools")"
if [[ ! -x "$relocated_gsc" ]]; then
  printf 'relocated Gerbil compiler driver is missing or not executable: %s\n' \
    "$relocated_gsc" >&2
  exit 69
fi
relocated_version="$(env GERBIL_HOME="$relocated_home" "$relocated_gxi" --version)"
if [[ "$relocated_version" != "$version" ]]; then
  printf 'relocated Gerbil version mismatch: expected %s, got %s\n' \
    "$version" "$relocated_version" >&2
  exit 69
fi
if [[ "$(env GERBIL_HOME="$relocated_home" "$relocated_gxi" -e '(display "ready")')" != ready ]]; then
  printf 'relocated Gerbil runtime probe failed\n' >&2
  exit 70
fi
relocation_probe_source="$relocation_root/relocation-probe.ss"
relocation_probe_output="$relocation_root/relocation-probe-lib"
mkdir -p "$relocation_probe_output"
printf '%s\n' \
  '(export relocation-ready)' \
  "(def relocation-ready 'ready)" \
  >"$relocation_probe_source"
env \
  GERBIL_GCC="$cc" \
  GERBIL_GSC="$relocated_gsc" \
  GERBIL_HOME="$relocated_home" \
  "$relocated_gxc" -d "$relocation_probe_output" "$relocation_probe_source"
relocation_seconds="$((SECONDS - relocation_started_at))"

elapsed_seconds="$((SECONDS - started_at))"
jq -n \
  --arg schema gerbil-bazel.prebuilt-capability-package-receipt.v1 \
  --arg archive "$(basename "$archive")" \
  --arg archive_sha256 "$archive_sha256" \
  --arg capability_id "$capability_id" \
  --arg version "$version" \
  --arg system "$system" \
  --arg architecture "$architecture" \
  --argjson archive_seconds "$archive_seconds" \
  --argjson archive_size_bytes "$archive_size_bytes" \
  --argjson elapsed_seconds "$elapsed_seconds" \
  --argjson relocation_seconds "$relocation_seconds" \
  '{
    schema: $schema,
    outcome: "ready",
    archive: $archive,
    archiveSha256: $archive_sha256,
    archiveSizeBytes: $archive_size_bytes,
    capabilityId: $capability_id,
    version: $version,
    platform: {os: $system, arch: $architecture},
    relocationVerified: true,
    compilerRelocationVerified: true,
    archiveSeconds: $archive_seconds,
    relocationSeconds: $relocation_seconds,
    elapsedSeconds: $elapsed_seconds
  }' >"$output_stem.receipt.json"

jq -c . "$output_stem.receipt.json"
