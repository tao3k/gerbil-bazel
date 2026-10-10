#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
: "${GERBIL_PREFIX:?selected built prefix required}"
receipt="$GERBIL_PREFIX/ci-source-toolchain.json"
jq -e '.multipleVms == true and (.identity | type == "string") and
       (.platform == "darwin-aarch64" or .platform == "linux-x86_64")' "$receipt" >/dev/null
source "$GERBIL_PREFIX/activate"
revision=$(jq -r .sourceRevision "$receipt")
patchset=$(jq -r .patchsetHash "$receipt")
platform=$(jq -r .platform "$receipt")
profile=$(jq -r .buildProfile "$receipt")
version=$(gxi -v)
[[ "$version" == "Gerbil ${revision:0:7}"* ]]
identity_hash=$(jq -r .identity "$receipt" | shasum -a 256 | awk '{print $1}')
tag="gerbil-v0.19-$revision-$platform-$profile-patch${patchset:0:12}-build${identity_hash:0:12}"
output="${GERBIL_RELEASE_DIRECTORY:-$root/.ci/release}"
mkdir -p "$output"
stage=$(mktemp -d "$output/.capability.XXXXXX")
trap 'rm -rf "$stage"' EXIT
name="gerbil-v0.19-$platform"
cp -a "$GERBIL_PREFIX" "$stage/$name"
(unset GAMBOPT; source "$stage/$name/activate"; [[ $(gxi -v) == "$version" ]])
jq -n --arg version "$version" --arg revision "$revision" --arg patchset "$patchset" \
  --arg platform "$platform" --arg profile "$profile" \
  '{schema:"gerbil-bazel.toolchain-release.v1", version:$version,
    upstreamRevision:$revision, stagingRevision:$revision, ensembleRevision:$revision,
    patchsetSha:$patchset, buildProfile:$profile,
    platform:{os:($platform|split("-")[0]),arch:($platform|split("-")[1])},
    activation:"source ./activate"}' > "$stage/$name/gerbil-toolchain-release.json"
tar -czf "$output/$tag.tar.gz" -C "$stage" "$name"
(cd "$output"; shasum -a 256 "$tag.tar.gz" > "$tag.tar.gz.sha256")
sha=$(shasum -a 256 "$output/$tag.tar.gz" | awk '{print $1}')
jq --arg sha "$sha" --arg tag "$tag" '. + {archiveSha256:$sha, releaseTag:$tag}' \
  "$receipt" > "$output/$tag.json"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then printf 'tag=%s\n' "$tag" >> "$GITHUB_OUTPUT"; fi
printf 'CAPABILITY-PACKAGED %s\n' "$tag"
