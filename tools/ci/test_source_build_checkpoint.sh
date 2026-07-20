#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
source_root="$test_root/source"
checkpoint_root="$test_root/checkpoint"
prefix_root="$test_root/prefix"
identity_receipt="$test_root/source-build-identity.json"
schema="$repo_root/schemas/gerbil-bazel.source-build-checkpoint.v1.schema.json"
install_digest="$(printf 'a%.0s' {1..64})"
output_identity_digest="$(printf 'b%.0s' {1..64})"

mkdir -p "$source_root/build/bin" "$source_root/build/lib"
printf 'synthetic build environment\n' >"$source_root/build-env.sh"
cat >"$source_root/build/bin/gxi" <<'EOF'
#!/usr/bin/env bash
printf 'synthetic gxi\n'
EOF
chmod +x "$source_root/build/bin/gxi"
cp "$source_root/build/bin/gxi" "$source_root/build/bin/gxi-alias"
ln -s gxi "$source_root/build/bin/gxc"
printf 'safe stage1 output\n' >"$source_root/build/lib/stage1.scm"
git -C "$source_root" init --quiet
git -C "$source_root" add build-env.sh
git -C "$source_root" \
  -c user.name=gerbil-bazel \
  -c user.email=gerbil-bazel@example.invalid \
  commit --quiet -m fixture
source_ref="$(git -C "$source_root" rev-parse HEAD)"

jq -nS \
  --arg install_digest "$install_digest" \
  --arg output_identity_digest "$output_identity_digest" \
  --arg source_ref "$source_ref" \
  --arg source_url "$source_root" \
  '{
    schema: "gerbil-bazel.source-build-identity.v1",
    installDigest: $install_digest,
    source: {ref: $source_ref, url: $source_url},
    config: {
      outputIdentityDigest: $output_identity_digest,
      value: {
        outputIdentity: {
          stageBuild: {
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
          }
        }
      }
    }
  }' >"$identity_receipt"

jq -e '
  .additionalProperties == false and
  .properties.schema.const == "gerbil-bazel.source-build-checkpoint.v1" and
  .properties.outcome.const == "safe-boundary" and
  .properties.boundary.enum == ["stage1", "stdlib", "tools"] and
  .properties.boundaryIndex.enum == [4, 5, 10] and
  (.required | length) == 12
' "$schema" >/dev/null

checkpoint="$repo_root/tools/ci/source_build_checkpoint.sh"
"$checkpoint" save:stage1 \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" >/dev/null
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"
[[ "$(
  "$checkpoint" boundary \
    "$checkpoint_root" \
    "$source_root" \
    "$prefix_root" \
    "$identity_receipt"
)" == stage1 ]]

stage1_generation="$(jq -er '.generation' "$checkpoint_root/current.json")"
stage1_tree="$checkpoint_root/generations/$stage1_generation/tree"
stage1_manifest="$checkpoint_root/generations/$stage1_generation/tree.manifest"
gxc_link_target_hash="$(
  printf '%s' gxi | git -C "$stage1_tree" hash-object --stdin
)"
gxi_content_hash="$(
  git -C "$stage1_tree" hash-object --no-filters build/bin/gxi
)"
stage1_content_hash="$(
  git -C "$stage1_tree" hash-object --no-filters build/lib/stage1.scm
)"
grep -Fx "$(
  printf 'symlink\t%s\t./build/bin/gxc' "$gxc_link_target_hash"
)" "$stage1_manifest" >/dev/null
grep -Fx "$(
  printf 'file\t100755\t%s\t./build/bin/gxi' "$gxi_content_hash"
)" "$stage1_manifest" >/dev/null
grep -Fx "$(
  printf 'file\t100644\t%s\t./build/lib/stage1.scm' \
    "$stage1_content_hash"
)" "$stage1_manifest" >/dev/null
chmod 0644 "$stage1_tree/build/bin/gxi"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted an executable file with mode 100644\n' >&2
  exit 1
fi
chmod 0755 "$stage1_tree/build/bin/gxi"
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"
chmod 0755 "$stage1_tree/build/lib/stage1.scm"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a data file with mode 100755\n' >&2
  exit 1
fi
chmod 0644 "$stage1_tree/build/lib/stage1.scm"
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"
rm "$stage1_tree/build/bin/gxc"
ln -s gxi-alias "$stage1_tree/build/bin/gxc"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a symlink retargeted to equal content\n' >&2
  exit 1
fi
rm "$stage1_tree/build/bin/gxc"
cp "$stage1_tree/build/bin/gxi" "$stage1_tree/build/bin/gxc"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a symlink replaced by equal content\n' >&2
  exit 1
fi
rm "$stage1_tree/build/bin/gxc"
ln -s missing-gxi "$stage1_tree/build/bin/gxc"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a mutated symbolic-link target\n' >&2
  exit 1
fi
rm "$stage1_tree/build/bin/gxc"
ln -s gxi "$stage1_tree/build/bin/gxc"
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"
printf 'corrupt non-sentinel generated output\n' \
  >"$stage1_tree/build/lib/stage1.scm"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a mutated non-sentinel generated output\n' >&2
  exit 1
fi
printf 'safe stage1 output\n' >"$stage1_tree/build/lib/stage1.scm"
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"

printf 'TERM-truncated live output\n' >"$source_root/build/lib/stage1.scm"
printf 'unsafe partial output\n' >"$source_root/build/lib/partial.scm"
"$checkpoint" restore \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" >/dev/null
grep -Fx 'safe stage1 output' "$source_root/build/lib/stage1.scm" >/dev/null
[[ ! -e "$source_root/build/lib/partial.scm" ]]

mkdir -p "$source_root/build/lib/std"
printf 'complete stdlib output\n' >"$source_root/build/lib/std/synthetic.scm"
mkdir -p "$checkpoint_root/.generation.tmp.stale"
printf 'interrupted copy\n' >"$checkpoint_root/.generation.tmp.stale/partial"
"$checkpoint" save:stdlib \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" >/dev/null
[[ ! -e "$checkpoint_root/.generation.tmp.stale" ]]
[[ "$(
  "$checkpoint" boundary \
    "$checkpoint_root" \
    "$source_root" \
    "$prefix_root" \
    "$identity_receipt"
)" == stdlib ]]
generations=("$checkpoint_root"/generations/generation-*)
[[ "${#generations[@]}" -eq 1 ]]
current_generation="$(jq -er '.generation' "$checkpoint_root/current.json")"
current_receipt="$checkpoint_root/generations/$current_generation/receipt.json"
jq -e '
  .schema == "gerbil-bazel.source-build-checkpoint.v1" and
  .outcome == "safe-boundary" and
  .boundary == "stdlib" and
  .boundaryIndex == 5 and
  (keys | sort) == ([
    "boundary",
    "boundaryIndex",
    "checkpointBoundaries",
    "installDigest",
    "outcome",
    "outputIdentityDigest",
    "prefixRoot",
    "schema",
    "source",
    "sourceRoot",
    "stageSequence",
    "treeManifestDigest"
  ] | sort)
' "$current_receipt" >/dev/null

mismatch_receipt="$test_root/mismatch-identity.json"
jq '.installDigest = ("c" * 64)' "$identity_receipt" >"$mismatch_receipt"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$mismatch_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a mismatched installation identity\n' >&2
  exit 1
fi

if "$checkpoint" save:gambit \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" >/dev/null 2>&1; then
  printf 'checkpoint accepted a non-boundary stage\n' >&2
  exit 1
fi

cp "$checkpoint_root/current.json" "$test_root/current.json"
jq '.generation = "../escape"' \
  "$test_root/current.json" >"$checkpoint_root/current.json"
if "$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt" 2>/dev/null; then
  printf 'checkpoint accepted a path-traversal generation pointer\n' >&2
  exit 1
fi
cp "$test_root/current.json" "$checkpoint_root/current.json"
"$checkpoint" validate \
  "$checkpoint_root" \
  "$source_root" \
  "$prefix_root" \
  "$identity_receipt"

printf 'source build checkpoint policy: ok\n'
