#!/usr/bin/env bash
set -euo pipefail
directory=${1:?verified capability artifact directory required}
shopt -s nullglob
archives=("$directory"/*.tar.gz)
[[ ${#archives[@]} == 1 ]] || exit 1
archive=${archives[0]}
tag=$(basename "$archive" .tar.gz)
receipt="$directory/$tag.json"
[[ $(jq -r .releaseTag "$receipt") == "$tag" ]] || exit 1
(cd "$directory"; shasum -a 256 -c "$tag.tar.gz.sha256")
sha=$(shasum -a 256 "$archive" | awk '{print $1}')
[[ $(jq -r .archiveSha256 "$receipt") == "$sha" ]] || exit 1
if gh release view "$tag" >/dev/null 2>&1; then
  existing=$(mktemp -d)
  trap 'rm -rf "$existing"' EXIT
  gh release download "$tag" --pattern "$tag.json" --pattern "$tag.tar.gz.sha256" --dir "$existing"
  identity=$(jq -r .identity "$receipt")
  jq -e --arg identity "$identity" --arg tag "$tag" \
    '.identity == $identity and .releaseTag == $tag' "$existing/$tag.json" >/dev/null
  recorded=$(jq -r .archiveSha256 "$existing/$tag.json")
  [[ "$recorded" =~ ^[0-9a-f]{64}$ ]] || exit 1
  [[ $(awk '{print $1}' "$existing/$tag.tar.gz.sha256") == "$recorded" ]] || exit 1
  [[ $(awk '{print $2}' "$existing/$tag.tar.gz.sha256") == "$tag.tar.gz" ]] || exit 1
  printf 'IMMUTABLE-RELEASE-REUSED %s\n' "$tag"
else
  gh release create "$tag" "$archive" "$archive.sha256" "$receipt" \
    --target "${RELEASE_COMMIT:-${GITHUB_SHA:?exact checked-out commit required}}" --title "$tag" \
    --notes "Validated unified source toolchain. Exact source, Gambit, compiler, patchset and configure arguments are in the attached receipt."
fi
