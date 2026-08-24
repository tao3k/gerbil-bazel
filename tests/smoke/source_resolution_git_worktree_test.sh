#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 4 ]]; then
  echo "usage: $0 <receipt> <root-source> <tracked-submodule-source> <untracked-submodule-source>" >&2
  exit 2
fi

receipt="${TEST_SRCDIR:?}/$1"
root_source="${TEST_SRCDIR:?}/$2"
tracked_submodule_source="${TEST_SRCDIR:?}/$3"
untracked_submodule_source="${TEST_SRCDIR:?}/$4"

require_match() {
  local mode="$1"
  local pattern="$2"
  local path="$3"
  local label="$4"
  if ! grep "$mode" "$pattern" "$path"; then
    printf 'missing %s in %s\n' "$label" "$path" >&2
    sed -n '1,80p' "$path" >&2
    exit 1
  fi
}

require_match -Eq \
  '"resolutionMode"[[:space:]]*:[[:space:]]*"legacy-unique-source"' \
  "$receipt" resolution-mode
require_match -Eq \
  '"sourceFileCount"[[:space:]]*:[[:space:]]*6' \
  "$receipt" source-file-count
require_match -Fq '(export root-source)' "$root_source" root-source
require_match -Fq \
  '(export tracked-submodule-source)' \
  "$tracked_submodule_source" tracked-submodule-source
require_match -Fq \
  '(export untracked-submodule-source)' \
  "$untracked_submodule_source" untracked-submodule-source
