#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
read -r aliases_root < "$project_root/.data/d882-alias-root"
test -d "$aliases_root" || { printf 'Missing alias directory\n' >&2; exit 1; }
for name in gerbil-gambit-bootstrap-audit d881-staging-install; do
  target="$project_root/.data/$name"
  alias="$aliases_root/$name"
  test -d "$target" || { printf 'Missing durable directory: %s\n' "$target" >&2; exit 1; }
  if test -L "$alias"; then
    test "$(readlink "$alias")" = "$target" || {
      printf 'Refusing unrelated symlink: %s\n' "$alias" >&2; exit 1;
    }
  elif test -e "$alias"; then
    printf 'Refusing existing path: %s\n' "$alias" >&2
    exit 1
  else
    ln -s "$target" "$alias"
  fi
done
printf 'D882-DURABLE-BUILD-ALIASES-OK\n'
