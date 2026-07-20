#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

repository=tao3k/gerbil-bazel
head_sha="$(printf 'a%.0s' {1..40})"
install_digest="$(printf 'b%.0s' {1..64})"
artifact_name="gerbil-prebuilt-test-${install_digest}"
fixture_dir="$test_root/fixtures"
mkdir -p "$fixture_dir" "$test_root/bin"

cat >"$test_root/bin/gh" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == api ]] || exit 64
case "${2:-}" in
  */actions/runs/*/artifacts) file=artifacts.json ;;
  */actions/runs/*) file=run.json ;;
  */pulls/*) file=pr.json ;;
  *) exit 64 ;;
esac
exec /bin/cat "${FIXTURE_DIR:?}/$file"
EOF
chmod +x "$test_root/bin/gh"

write_artifacts() {
  local count=$1
  jq -n \
    --arg name "$artifact_name" \
    --argjson count "$count" \
    '{artifacts: [range(0; $count) | {name: $name, expired: false}]}' \
    >"$fixture_dir/artifacts.json"
}

write_main_run() {
  jq -n \
    --arg repository "$repository" \
    --arg head_sha "$head_sha" \
    '{
      name: "CI",
      conclusion: "success",
      event: "push",
      head_branch: "main",
      head_sha: $head_sha,
      head_repository: {full_name: $repository},
      pull_requests: []
    }' >"$fixture_dir/run.json"
}

write_pr_run() {
  jq -n \
    --arg repository "$repository" \
    --arg head_sha "$head_sha" \
    '{
      name: "CI",
      conclusion: "success",
      event: "pull_request",
      head_branch: "feature/capability",
      head_sha: $head_sha,
      head_repository: {full_name: $repository},
      pull_requests: [{number: 9}]
    }' >"$fixture_dir/run.json"
}

write_pr() {
  jq -n \
    --arg repository "$repository" \
    --arg head_sha "$head_sha" \
    '{
      number: 9,
      state: "open",
      base: {ref: "main", repo: {full_name: $repository}},
      head: {
        ref: "feature/capability",
        sha: $head_sha,
        repo: {full_name: $repository}
      }
    }' >"$fixture_dir/pr.json"
}

run_authorized() {
  local name=$1
  local expected_authorization=$2
  local receipt="$test_root/$name.json"
  ARTIFACT_NAME="$artifact_name" \
    EXPECTED_HEAD_SHA="$head_sha" \
    EXPECTED_INSTALL_DIGEST="$install_digest" \
    FIXTURE_DIR="$fixture_dir" \
    GERBIL_PROMOTION_AUTHORIZATION_RECEIPT="$receipt" \
    GERBIL_PROMOTION_GH_COMMAND="$test_root/bin/gh" \
    REPOSITORY="$repository" \
    SOURCE_RUN_ID=101 \
    "$repo_root/tools/ci/authorize_prebuilt_promotion.sh" >/dev/null
  jq -e \
    --arg expected_authorization "$expected_authorization" \
    --arg install_digest "$install_digest" \
    '.schema == "gerbil-bazel.prebuilt-promotion-authorization.v1" and
     .outcome == "authorized" and
     .authorization == $expected_authorization and
     .installDigest == $install_digest and
     .artifact.count == 1 and
     .artifact.expired == false' \
    "$receipt" >/dev/null
}

assert_rejected() {
  local name=$1
  if ARTIFACT_NAME="$artifact_name" \
    EXPECTED_HEAD_SHA="$head_sha" \
    EXPECTED_INSTALL_DIGEST="$install_digest" \
    FIXTURE_DIR="$fixture_dir" \
    GERBIL_PROMOTION_AUTHORIZATION_RECEIPT="$test_root/rejected-$name.json" \
    GERBIL_PROMOTION_GH_COMMAND="$test_root/bin/gh" \
    REPOSITORY="$repository" \
    SOURCE_RUN_ID=101 \
    "$repo_root/tools/ci/authorize_prebuilt_promotion.sh" >/dev/null 2>&1; then
    printf 'promotion authorization accepted invalid fixture: %s\n' "$name" >&2
    exit 1
  fi
}

write_artifacts 1
write_main_run
run_authorized main main-branch

write_pr_run
write_pr
run_authorized same-repository-pr same-repository-pull-request
jq -e '.pullRequest.number == 9 and .pullRequest.baseRef == "main"' \
  "$test_root/same-repository-pr.json" >/dev/null

jq '.head.repo.full_name = "fork/gerbil-bazel"' \
  "$fixture_dir/pr.json" >"$fixture_dir/pr.tmp"
mv "$fixture_dir/pr.tmp" "$fixture_dir/pr.json"
assert_rejected fork-pr

write_pr
jq '.base.ref = "release"' "$fixture_dir/pr.json" >"$fixture_dir/pr.tmp"
mv "$fixture_dir/pr.tmp" "$fixture_dir/pr.json"
assert_rejected non-main-base

write_pr
jq '.state = "closed"' "$fixture_dir/pr.json" >"$fixture_dir/pr.tmp"
mv "$fixture_dir/pr.tmp" "$fixture_dir/pr.json"
assert_rejected closed-pr

write_pr
write_artifacts 2
assert_rejected duplicate-artifact

write_artifacts 1
jq '.artifacts[0].expired = true' \
  "$fixture_dir/artifacts.json" >"$fixture_dir/artifacts.tmp"
mv "$fixture_dir/artifacts.tmp" "$fixture_dir/artifacts.json"
assert_rejected expired-artifact

write_artifacts 1
write_pr_run
jq '.pull_requests += [{number: 10}]' \
  "$fixture_dir/run.json" >"$fixture_dir/run.tmp"
mv "$fixture_dir/run.tmp" "$fixture_dir/run.json"
assert_rejected ambiguous-pull-request

write_main_run
jq '.head_branch = "feature/capability"' \
  "$fixture_dir/run.json" >"$fixture_dir/run.tmp"
mv "$fixture_dir/run.tmp" "$fixture_dir/run.json"
assert_rejected non-main-push

write_pr_run
jq '.head_sha = "cccccccccccccccccccccccccccccccccccccccc"' \
  "$fixture_dir/run.json" >"$fixture_dir/run.tmp"
mv "$fixture_dir/run.tmp" "$fixture_dir/run.json"
assert_rejected head-sha-drift
