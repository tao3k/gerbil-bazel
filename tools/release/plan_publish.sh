#!/usr/bin/env bash
set -euo pipefail
platform=${PLATFORM:-both}
revision=$(jq -r .gerbilRevision tools/toolchain/profile.json)
[[ -z "${UPSTREAM_REF:-}" || "$UPSTREAM_REF" == "$revision" ]]
commit=$(git rev-parse HEAD)
source_run=${SOURCE_RUN:-}
if [[ -n "$source_run" ]]; then
  [[ "$source_run" =~ ^[0-9]+$ ]]
  gh api "repos/${GITHUB_REPOSITORY:?}/actions/runs/$source_run" \
    --jq '{head_sha,head_branch,conclusion,name,event}' | \
    jq -e --arg sha "$commit" '.head_sha == $sha and .head_branch == "main" and
      .conclusion == "success" and .name == "CI" and .event == "push"'
fi
matrix=$(jq -cn --arg platform "$platform" --arg source_run "$source_run" \
  '{include:[{platform:"linux-x86_64",runner:"ubuntu-latest",os:"Linux"},
             {platform:"darwin-aarch64",runner:"macos-26",os:"macOS"}] |
    map(select($platform == "both" or .platform == $platform))} |
    if $source_run != "" then .include[].runner = "ubuntu-latest" else . end')
[[ $(jq '.include|length' <<< "$matrix") -gt 0 ]]
printf 'matrix=%s\ncommit=%s\nsource_run=%s\n' "$matrix" "$commit" "$source_run" >> "${GITHUB_OUTPUT:?}"
