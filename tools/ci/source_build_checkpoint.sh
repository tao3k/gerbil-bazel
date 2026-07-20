#!/usr/bin/env bash
set -euo pipefail

if (( $# != 5 )); then
  printf '%s\n' \
    "usage: source_build_checkpoint.sh COMMAND CHECKPOINT_ROOT SOURCE_ROOT PREFIX_ROOT IDENTITY_RECEIPT" \
    >&2
  exit 64
fi

command_name=$1
checkpoint_root=$2
source_root=$3
prefix_root=$4
identity_receipt=$5

case "$command_name" in
  validate | restore | boundary) ;;
  save:*) ;;
  *)
    printf 'unknown source-build checkpoint command: %s\n' "$command_name" >&2
    exit 64
    ;;
esac

if ! identity_json="$(
  jq -cSe '
    select(.schema == "gerbil-bazel.source-build-identity.v1") |
    select(.installDigest | test("^[0-9a-f]{64}$")) |
    select(.config.outputIdentityDigest | test("^[0-9a-f]{64}$")) |
    select(.source.ref | type == "string" and length > 0) |
    select(.source.url | type == "string" and length > 0) |
    select(.config.value.outputIdentity.stageBuild == {
      strategy: "upstream-exposed-stage-sequence",
      sequence: [
        "prepare",
        "gambit",
        "boot-gxi",
        "stage0",
        "stage1",
        "stdlib",
        "libgerbil",
        "lang",
        "r7rs-large",
        "srfi",
        "tools"
      ],
      checkpointBoundaries: ["stage1", "stdlib", "tools"],
      checkpointSchema: "gerbil-bazel.source-build-checkpoint.v1"
    })
  ' "$identity_receipt"
)"; then
  printf 'source-build checkpoint identity is invalid: %s\n' \
    "$identity_receipt" >&2
  exit 65
fi

install_digest="$(jq -er '.installDigest' <<<"$identity_json")"
output_identity_digest="$(
  jq -er '.config.outputIdentityDigest' <<<"$identity_json"
)"
source_ref="$(jq -er '.source.ref' <<<"$identity_json")"
source_url="$(jq -er '.source.url' <<<"$identity_json")"
stage_sequence="$(
  jq -cS '.config.value.outputIdentity.stageBuild.sequence' <<<"$identity_json"
)"
checkpoint_boundaries="$(
  jq -cS '.config.value.outputIdentity.stageBuild.checkpointBoundaries' \
    <<<"$identity_json"
)"
pointer_path="$checkpoint_root/current.json"

sha256_file() {
  local path=$1
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
  else
    shasum -a 256 "$path" | awk '{print $1}'
  fi
}

write_tree_manifest() {
  local tree_root=$1
  local output_path=$2
  local paths_path
  local regular_paths_path
  local regular_modes_path
  local symlink_paths_path
  local hashes_path
  local path_count
  local mode_count
  local hash_count
  local mode
  local hash
  local path
  local link_target_hash

  paths_path="$(mktemp "${TMPDIR:-/tmp}/gerbil-checkpoint-paths.XXXXXX")"
  regular_paths_path="$(
    mktemp "${TMPDIR:-/tmp}/gerbil-checkpoint-regular-paths.XXXXXX"
  )"
  regular_modes_path="$(
    mktemp "${TMPDIR:-/tmp}/gerbil-checkpoint-regular-modes.XXXXXX"
  )"
  symlink_paths_path="$(
    mktemp "${TMPDIR:-/tmp}/gerbil-checkpoint-symlink-paths.XXXXXX"
  )"
  hashes_path="$(mktemp "${TMPDIR:-/tmp}/gerbil-checkpoint-hashes.XXXXXX")"
  if ! (
    cd "$tree_root"
    LC_ALL=C find . \
      -path './.git' -prune -o \
      \( -type f -o -type l \) -print \
      | LC_ALL=C sort >"$paths_path"
    : >"$regular_paths_path"
    : >"$regular_modes_path"
    : >"$symlink_paths_path"
    while IFS= read -r path; do
      if [[ -L "$path" ]]; then
        printf '%s\n' "$path" >>"$symlink_paths_path"
      elif [[ -f "$path" ]]; then
        printf '%s\n' "$path" >>"$regular_paths_path"
        if [[ -x "$path" ]]; then
          printf '100755\n' >>"$regular_modes_path"
        else
          printf '100644\n' >>"$regular_modes_path"
        fi
      else
        printf 'checkpoint manifest path changed during traversal: %s\n' \
          "$path" >&2
        exit 1
      fi
    done <"$paths_path"
    git hash-object --no-filters --stdin-paths \
      <"$regular_paths_path" >"$hashes_path"
  ); then
    rm -f \
      "$paths_path" \
      "$regular_paths_path" \
      "$regular_modes_path" \
      "$symlink_paths_path" \
      "$hashes_path"
    return 1
  fi
  path_count="$(wc -l <"$regular_paths_path" | tr -d ' ')"
  mode_count="$(wc -l <"$regular_modes_path" | tr -d ' ')"
  hash_count="$(wc -l <"$hashes_path" | tr -d ' ')"
  if [[ "$path_count" != "$mode_count" ]] ||
     [[ "$path_count" != "$hash_count" ]]; then
    rm -f \
      "$paths_path" \
      "$regular_paths_path" \
      "$regular_modes_path" \
      "$symlink_paths_path" \
      "$hashes_path"
    printf 'checkpoint manifest path/mode/hash count mismatch: %s/%s/%s\n' \
      "$path_count" "$mode_count" "$hash_count" >&2
    return 1
  fi
  : >"$output_path"
  while IFS=$'\t' read -r mode hash path; do
    printf 'file\t%s\t%s\t%s\n' "$mode" "$hash" "$path"
  done < <(
    paste "$regular_modes_path" "$hashes_path" "$regular_paths_path"
  ) >>"$output_path"
  if ! (
    cd "$tree_root"
    while IFS= read -r path; do
      link_target_hash="$(
        readlink -n "$path" | git hash-object --stdin
      )" || exit 1
      printf 'symlink\t%s\t%s\n' "$link_target_hash" "$path"
    done <"$symlink_paths_path"
  ) >>"$output_path"; then
    rm -f \
      "$paths_path" \
      "$regular_paths_path" \
      "$regular_modes_path" \
      "$symlink_paths_path" \
      "$hashes_path"
    return 1
  fi
  rm -f \
    "$paths_path" \
    "$regular_paths_path" \
    "$regular_modes_path" \
    "$symlink_paths_path" \
    "$hashes_path"
}

absolute_path() {
  local path=$1
  local parent
  local name
  parent="$(dirname "$path")"
  name="$(basename "$path")"
  mkdir -p "$parent"
  printf '%s/%s\n' "$(cd "$parent" && pwd -P)" "$name"
}

source_root="$(absolute_path "$source_root")"
prefix_root="$(absolute_path "$prefix_root")"
checkpoint_root="$(absolute_path "$checkpoint_root")"
pointer_path="$checkpoint_root/current.json"

stage_index() {
  local stage=$1
  jq -er \
    --arg stage "$stage" \
    'to_entries[] | select(.value == $stage) | .key' \
    <<<"$stage_sequence"
}

validate_checkpoint() {
  local generation
  local generation_root
  local receipt
  local boundary
  local boundary_index
  local observed_head
  local expected_manifest_digest
  local observed_manifest_digest
  local manifest_path
  local manifest_tmp

  generation="$(
    jq -er '
      select(.schema == "gerbil-bazel.source-build-checkpoint-pointer.v1") |
      .generation |
      select(type == "string") |
      select(test("^generation-[A-Za-z0-9._-]+$"))
    ' "$pointer_path" 2>/dev/null
  )" || return 1
  generation_root="$checkpoint_root/generations/$generation"
  receipt="$generation_root/receipt.json"
  manifest_path="$generation_root/tree.manifest"
  [[ -d "$generation_root/tree/.git" ]] || return 1

  expected_manifest_digest="$(
    jq -er '.treeManifestDigest | select(test("^[0-9a-f]{64}$"))' \
      "$receipt" 2>/dev/null
  )" || return 1
  [[ -f "$manifest_path" ]] || return 1
  observed_manifest_digest="$(sha256_file "$manifest_path")" || return 1
  [[ "$observed_manifest_digest" == "$expected_manifest_digest" ]] || return 1
  manifest_tmp="$(mktemp "$checkpoint_root/.validate-manifest.tmp.XXXXXX")"
  if ! write_tree_manifest "$generation_root/tree" "$manifest_tmp" ||
     ! cmp -s "$manifest_path" "$manifest_tmp"; then
    rm -f "$manifest_tmp"
    return 1
  fi
  rm -f "$manifest_tmp"

  boundary="$(jq -er '.boundary' "$receipt" 2>/dev/null)" || return 1
  boundary_index="$(stage_index "$boundary")" || return 1
  jq -e \
    --arg install_digest "$install_digest" \
    --arg output_identity_digest "$output_identity_digest" \
    --arg source_ref "$source_ref" \
    --arg source_url "$source_url" \
    --arg source_root "$source_root" \
    --arg prefix_root "$prefix_root" \
    --arg tree_manifest_digest "$expected_manifest_digest" \
    --arg boundary "$boundary" \
    --argjson boundary_index "$boundary_index" \
    --argjson stage_sequence "$stage_sequence" \
    --argjson checkpoint_boundaries "$checkpoint_boundaries" \
    'select(.schema == "gerbil-bazel.source-build-checkpoint.v1") |
     select(.outcome == "safe-boundary") |
     select(.installDigest == $install_digest) |
     select(.outputIdentityDigest == $output_identity_digest) |
     select(.source == {ref: $source_ref, url: $source_url}) |
     select(.sourceRoot == $source_root) |
     select(.prefixRoot == $prefix_root) |
     select(.treeManifestDigest == $tree_manifest_digest) |
     select(.boundary == $boundary) |
     select(.boundaryIndex == $boundary_index) |
     select(.stageSequence == $stage_sequence) |
     select(.checkpointBoundaries == $checkpoint_boundaries)' \
    "$receipt" >/dev/null || return 1

  jq -e --arg boundary "$boundary" 'index($boundary) != null' \
    <<<"$checkpoint_boundaries" >/dev/null || return 1
  observed_head="$(
    git -C "$generation_root/tree" rev-parse HEAD 2>/dev/null
  )" || return 1
  [[ "$observed_head" == "$source_ref" ]] || return 1
  [[ -f "$generation_root/tree/build-env.sh" ]] || return 1
  [[ -x "$generation_root/tree/build/bin/gxi" ]] || return 1
  if [[ "$boundary" == stdlib || "$boundary" == tools ]]; then
    [[ -d "$generation_root/tree/build/lib/std" ]] || return 1
  fi

  printf '%s\n' "$generation_root"
}

save_checkpoint() {
  local boundary=$1
  local boundary_index
  local generation
  local generation_tmp
  local generation_root
  local pointer_tmp
  local observed_head
  local old_generation
  local stale_generation
  local tree_manifest_digest

  cleanup_generation_tmp() {
    if [[ -n "${generation_tmp:-}" && -d "$generation_tmp" ]]; then
      rm -rf -- "$generation_tmp"
    fi
  }

  boundary_index="$(stage_index "$boundary")" || {
    printf 'unknown checkpoint boundary: %s\n' "$boundary" >&2
    return 64
  }
  jq -e --arg boundary "$boundary" 'index($boundary) != null' \
    <<<"$checkpoint_boundaries" >/dev/null || {
      printf 'stage is not an authorized checkpoint boundary: %s\n' \
        "$boundary" >&2
      return 64
    }
  observed_head="$(git -C "$source_root" rev-parse HEAD 2>/dev/null)" || {
    printf 'checkpoint source tree is not a Git checkout: %s\n' \
      "$source_root" >&2
    return 65
  }
  [[ "$observed_head" == "$source_ref" ]] || {
    printf 'checkpoint source revision mismatch: expected %s, observed %s\n' \
      "$source_ref" "$observed_head" >&2
    return 65
  }
  [[ -f "$source_root/build-env.sh" ]] || return 65
  [[ -x "$source_root/build/bin/gxi" ]] || return 65
  if [[ "$boundary" == stdlib || "$boundary" == tools ]]; then
    [[ -d "$source_root/build/lib/std" ]] || return 65
  fi

  mkdir -p "$checkpoint_root/generations"
  for stale_generation in "$checkpoint_root"/.generation.tmp.*; do
    [[ -e "$stale_generation" ]] || continue
    rm -rf -- "$stale_generation"
  done
  generation_tmp="$(mktemp -d "$checkpoint_root/.generation.tmp.XXXXXX")"
  trap cleanup_generation_tmp EXIT
  mkdir -p "$generation_tmp/tree"
  cp -a "$source_root/." "$generation_tmp/tree/"
  [[ "$(git -C "$generation_tmp/tree" rev-parse HEAD)" == "$source_ref" ]]
  write_tree_manifest \
    "$generation_tmp/tree" \
    "$generation_tmp/tree.manifest"
  tree_manifest_digest="$(sha256_file "$generation_tmp/tree.manifest")"
  jq -nS \
    --arg schema gerbil-bazel.source-build-checkpoint.v1 \
    --arg install_digest "$install_digest" \
    --arg output_identity_digest "$output_identity_digest" \
    --arg source_ref "$source_ref" \
    --arg source_url "$source_url" \
    --arg source_root "$source_root" \
    --arg prefix_root "$prefix_root" \
    --arg tree_manifest_digest "$tree_manifest_digest" \
    --arg boundary "$boundary" \
    --argjson boundary_index "$boundary_index" \
    --argjson stage_sequence "$stage_sequence" \
    --argjson checkpoint_boundaries "$checkpoint_boundaries" \
    '{
      schema: $schema,
      outcome: "safe-boundary",
      installDigest: $install_digest,
      outputIdentityDigest: $output_identity_digest,
      source: {ref: $source_ref, url: $source_url},
      sourceRoot: $source_root,
      prefixRoot: $prefix_root,
      treeManifestDigest: $tree_manifest_digest,
      boundary: $boundary,
      boundaryIndex: $boundary_index,
      stageSequence: $stage_sequence,
      checkpointBoundaries: $checkpoint_boundaries
    }' >"$generation_tmp/receipt.json"

  generation="generation-${boundary}-$(date +%s)-$$"
  generation_root="$checkpoint_root/generations/$generation"
  mv "$generation_tmp" "$generation_root"
  generation_tmp=
  trap - EXIT
  pointer_tmp="$(mktemp "$checkpoint_root/.current.json.tmp.XXXXXX")"
  jq -nS \
    --arg generation "$generation" \
    '{
      schema: "gerbil-bazel.source-build-checkpoint-pointer.v1",
      generation: $generation
    }' >"$pointer_tmp"
  mv "$pointer_tmp" "$pointer_path"

  for old_generation in "$checkpoint_root"/generations/generation-*; do
    [[ -e "$old_generation" ]] || continue
    if [[ "$(basename "$old_generation")" != "$generation" ]]; then
      rm -rf -- "$old_generation"
    fi
  done
  jq -c . "$generation_root/receipt.json"
}

case "$command_name" in
  save:*)
    save_checkpoint "${command_name#save:}"
    ;;
  validate)
    validate_checkpoint >/dev/null
    ;;
  boundary)
    generation_root="$(validate_checkpoint)"
    jq -er '.boundary' "$generation_root/receipt.json"
    ;;
  restore)
    generation_root="$(validate_checkpoint)"
    source_parent="$(dirname "$source_root")"
    source_name="$(basename "$source_root")"
    restore_tmp="$(mktemp -d "$source_parent/.$source_name.restore.XXXXXX")"
    restore_manifest="$(mktemp "$source_parent/.$source_name.manifest.XXXXXX")"
    trap 'rm -rf "$restore_tmp"; rm -f "$restore_manifest"' EXIT
    cp -a "$generation_root/tree/." "$restore_tmp/"
    [[ "$(git -C "$restore_tmp" rev-parse HEAD)" == "$source_ref" ]]
    write_tree_manifest "$restore_tmp" "$restore_manifest"
    cmp -s "$generation_root/tree.manifest" "$restore_manifest"
    rm -f "$restore_manifest"
    rm -rf -- "$source_root"
    mv "$restore_tmp" "$source_root"
    trap - EXIT
    jq -er '.boundary' "$generation_root/receipt.json"
    ;;
esac
