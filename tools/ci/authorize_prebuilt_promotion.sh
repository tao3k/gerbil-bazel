#!/usr/bin/env bash
set -euo pipefail

: "${ARTIFACT_NAME:?ARTIFACT_NAME is required}"
: "${EXPECTED_HEAD_SHA:?EXPECTED_HEAD_SHA is required}"
: "${EXPECTED_INSTALL_DIGEST:?EXPECTED_INSTALL_DIGEST is required}"
: "${REPOSITORY:?REPOSITORY is required}"
: "${SOURCE_RUN_ID:?SOURCE_RUN_ID is required}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
gh_command="${GERBIL_PROMOTION_GH_COMMAND:-gh}"
receipt_path="${GERBIL_PROMOTION_AUTHORIZATION_RECEIPT:-$repo_root/.ci/receipts/prebuilt-promotion-authorization.json}"

if [[ ! "$SOURCE_RUN_ID" =~ ^[1-9][0-9]*$ ]]; then
  printf 'invalid source run id: %s\n' "$SOURCE_RUN_ID" >&2
  exit 64
fi
if [[ ! "$EXPECTED_HEAD_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'invalid expected head SHA: %s\n' "$EXPECTED_HEAD_SHA" >&2
  exit 64
fi
if [[ ! "$EXPECTED_INSTALL_DIGEST" =~ ^[0-9a-f]{64}$ ]]; then
  printf 'invalid expected installation digest: %s\n' \
    "$EXPECTED_INSTALL_DIGEST" >&2
  exit 64
fi
if [[ ! "$REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  printf 'invalid repository identity: %s\n' "$REPOSITORY" >&2
  exit 64
fi

run_json="$("$gh_command" api "repos/${REPOSITORY}/actions/runs/${SOURCE_RUN_ID}")"
artifacts_json="$("$gh_command" api "repos/${REPOSITORY}/actions/runs/${SOURCE_RUN_ID}/artifacts")"

if ! jq -e \
  --arg repository "$REPOSITORY" \
  --arg expected_head_sha "$EXPECTED_HEAD_SHA" \
  '.name == "CI" and
   .conclusion == "success" and
   .head_sha == $expected_head_sha and
   .head_repository.full_name == $repository' \
  <<<"$run_json" >/dev/null; then
  printf 'source run identity is not an authorized capability producer\n' >&2
  exit 1
fi

artifact_count="$(
  jq -er \
    --arg artifact_name "$ARTIFACT_NAME" \
    '[.artifacts[] | select(.name == $artifact_name and .expired == false)] | length' \
    <<<"$artifacts_json"
)"
if [[ "$artifact_count" != 1 ]]; then
  printf 'source run must contain exactly one live capability artifact: %s\n' \
    "$ARTIFACT_NAME" >&2
  exit 1
fi

event="$(jq -er .event <<<"$run_json")"
head_branch="$(jq -er .head_branch <<<"$run_json")"
authorization=
pull_request_json=null

case "$event" in
  push | workflow_dispatch)
    if [[ "$head_branch" != main ]]; then
      printf 'main-branch producer event resolved from non-main branch: %s\n' \
        "$head_branch" >&2
      exit 1
    fi
    authorization=main-branch
    ;;
  pull_request)
    pull_request_count="$(jq -er '.pull_requests | length' <<<"$run_json")"
    if [[ "$pull_request_count" != 1 ]]; then
      printf 'pull-request producer must resolve exactly one pull request\n' >&2
      exit 1
    fi
    pull_request_number="$(jq -er '.pull_requests[0].number' <<<"$run_json")"
    pr_json="$("$gh_command" api "repos/${REPOSITORY}/pulls/${pull_request_number}")"
    if ! jq -e \
      --arg repository "$REPOSITORY" \
      --arg expected_head_sha "$EXPECTED_HEAD_SHA" \
      --arg head_branch "$head_branch" \
      --argjson pull_request_number "$pull_request_number" \
      '.number == $pull_request_number and
       .state == "open" and
       .base.ref == "main" and
       .base.repo.full_name == $repository and
       .head.ref == $head_branch and
       .head.sha == $expected_head_sha and
       .head.repo.full_name == $repository' \
      <<<"$pr_json" >/dev/null; then
      printf 'pull-request producer is not an open same-repository main-base PR\n' >&2
      exit 1
    fi
    authorization=same-repository-pull-request
    pull_request_json="$(
      jq -cS \
        '{number, state, headRef: .head.ref, headSha: .head.sha,
          headRepository: .head.repo.full_name, baseRef: .base.ref,
          baseRepository: .base.repo.full_name}' \
        <<<"$pr_json"
    )"
    ;;
  *)
    printf 'unsupported source producer event: %s\n' "$event" >&2
    exit 1
    ;;
esac

mkdir -p "$(dirname "$receipt_path")"
jq -nS \
  --arg schema gerbil-bazel.prebuilt-promotion-authorization.v1 \
  --arg authorization "$authorization" \
  --arg repository "$REPOSITORY" \
  --arg install_digest "$EXPECTED_INSTALL_DIGEST" \
  --argjson source_run_id "$SOURCE_RUN_ID" \
  --arg event "$event" \
  --arg head_branch "$head_branch" \
  --arg head_sha "$EXPECTED_HEAD_SHA" \
  --arg artifact_name "$ARTIFACT_NAME" \
  --argjson pull_request "$pull_request_json" \
  '{
    schema: $schema,
    outcome: "authorized",
    authorization: $authorization,
    repository: $repository,
    installDigest: $install_digest,
    sourceRun: {
      id: $source_run_id,
      workflow: "CI",
      event: $event,
      headBranch: $head_branch,
      headSha: $head_sha,
      headRepository: $repository
    },
    artifact: {name: $artifact_name, count: 1, expired: false}
  } +
  (if $pull_request == null then {} else {pullRequest: $pull_request} end)' \
  >"$receipt_path"

jq -c . "$receipt_path"
