#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
workflow="$repo_root/.github/workflows/source-producer.yml"

ruby -ryaml - "$workflow" <<'RUBY'
workflow_path = ARGV.fetch(0)
workflow = Psych.safe_load(File.read(workflow_path), aliases: true)
job = workflow.fetch("jobs").fetch("linux-capability")
steps = job.fetch("steps")

def assert(condition, message)
  raise message unless condition
end

def step_named(steps, name)
  steps.find { |step| step["name"] == name } || raise("missing workflow step: #{name}")
end

def normalized(expression)
  expression.to_s.gsub(/\s+/, " ").strip
end

cache_sha = "55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
restore = step_named(steps, "Restore Linux compiler cache")
installation = step_named(steps, "Restore Linux Gerbil installation")
checkpoint_restore = step_named(steps, "Restore Linux source-build checkpoint")
build = step_named(steps, "Build Gerbil on Linux")
save = step_named(steps, "Save Linux compiler cache")
checkpoint_save = step_named(steps, "Save Linux source-build checkpoint")
materialization = step_named(steps, "Record Linux Gerbil materialization")

assert(restore["id"] == "gerbil-compiler-cache", "compiler-cache restore id drifted")
assert(restore["uses"] == "actions/cache/restore@#{cache_sha}", "compiler-cache restore action drifted")
assert(restore.fetch("with").fetch("path") == ".ci/ccache", "compiler-cache restore path drifted")
assert(
  restore.fetch("with").fetch("key") ==
    "gerbil-ccache-${{ runner.os }}-${{ runner.arch }}-${{ steps.gerbil-source-build-identity.outputs.compiler_cache_namespace_digest }}-${{ github.run_id }}-${{ github.run_attempt }}",
  "compiler-cache primary key must rotate by run id and run attempt"
)

restore_keys = restore.fetch("with").fetch("restore-keys").lines.map(&:strip).reject(&:empty?)
assert(
  restore_keys == [
    "gerbil-ccache-${{ runner.os }}-${{ runner.arch }}-${{ steps.gerbil-source-build-identity.outputs.compiler_cache_namespace_digest }}-",
    "gerbil-ccache-${{ runner.os }}-${{ runner.arch }}-${{ env.GERBIL_VERSION_LABEL }}-",
  ],
  "compiler-cache restore-key priority drifted"
)

assert(
  installation["uses"] == "actions/cache@#{cache_sha}",
  "complete installation cache must retain the combined atomic cache action"
)
assert(installation["id"] == "gerbil-install-cache", "installation-cache id drifted")
assert(installation.fetch("with").fetch("path") == ".ci/gerbil-prefix", "installation-cache path drifted")
assert(
  installation.fetch("with").fetch("key") ==
    "gerbil-install-v1-${{ steps.gerbil-source-build-identity.outputs.install_digest }}",
  "installation cache must remain keyed only by the exact install digest"
)

assert(
  checkpoint_restore["uses"] == "actions/cache/restore@#{cache_sha}",
  "source-build checkpoint restore action drifted"
)
assert(
  checkpoint_restore["id"] == "gerbil-source-build-checkpoint",
  "source-build checkpoint restore id drifted"
)
assert(
  normalized(checkpoint_restore["if"]) ==
    "steps.gerbil-install-cache.outputs.cache-hit != 'true'",
  "installation cache must supersede source-build checkpoint restore"
)
assert(
  checkpoint_restore.fetch("with").fetch("path") ==
    ".ci/gerbil-source-build-checkpoint",
  "source-build checkpoint restore path drifted"
)
assert(
  checkpoint_restore.fetch("with").fetch("key") ==
    "gerbil-source-build-checkpoint-v1-${{ steps.gerbil-source-build-identity.outputs.install_digest }}-${{ github.run_id }}-${{ github.run_attempt }}",
  "source-build checkpoint key must bind exact identity and rotate per attempt"
)
assert(
  checkpoint_restore.fetch("with").fetch("restore-keys").lines.map(&:strip).reject(&:empty?) == [
    "gerbil-source-build-checkpoint-v1-${{ steps.gerbil-source-build-identity.outputs.install_digest }}-",
  ],
  "source-build checkpoint must restore only the exact installation identity"
)

assert(build["id"] == "gerbil-build", "Gerbil build step id drifted")
assert(
  normalized(build["if"]) == "steps.gerbil-install-cache.outputs.cache-hit != 'true'",
  "Gerbil build must remain gated only by an exact installation-cache miss"
)

assert(save["uses"] == "actions/cache/save@#{cache_sha}", "compiler-cache save action drifted")
assert(save["continue-on-error"] == true, "compiler-cache save must remain non-authoritative")
assert(save.fetch("with").fetch("path") == ".ci/ccache", "compiler-cache save path drifted")
assert(
  save.fetch("with").fetch("key") == "${{ steps.gerbil-compiler-cache.outputs.cache-primary-key }}",
  "compiler-cache save must use the restore action's primary key"
)
assert(
  normalized(save["if"]) ==
    "always() && steps.gerbil-install-cache.outputs.cache-hit != 'true' && " \
    "(steps.gerbil-build.outcome == 'success' || steps.gerbil-build.outcome == 'failure')",
  "compiler-cache save must run only after a completed build success or failure"
)

assert(
  checkpoint_save["uses"] == "actions/cache/save@#{cache_sha}",
  "source-build checkpoint save action drifted"
)
assert(
  checkpoint_save["continue-on-error"] == true,
  "source-build checkpoint cache must remain non-authoritative"
)
assert(
  checkpoint_save.fetch("with").fetch("path") ==
    ".ci/gerbil-source-build-checkpoint",
  "source-build checkpoint save path drifted"
)
assert(
  checkpoint_save.fetch("with").fetch("key") ==
    "${{ steps.gerbil-source-build-checkpoint.outputs.cache-primary-key }}",
  "source-build checkpoint save must use the restore primary key"
)
assert(
  normalized(checkpoint_save["if"]) ==
    "always() && steps.gerbil-install-cache.outputs.cache-hit != 'true' && " \
    "steps.gerbil-build.outcome == 'failure' && " \
    "steps.gerbil-build.outputs.checkpoint_available == 'true'",
  "source-build checkpoint may save only a validated safe boundary after failure"
)
assert(
  build.fetch("env").fetch("GERBIL_SOURCE_BUILD_CHECKPOINT_ROOT") ==
    "${{ github.workspace }}/.ci/gerbil-source-build-checkpoint",
  "build step must use the declared checkpoint root"
)
assert(
  build.fetch("run").include?("checkpoint_available=$checkpoint_available"),
  "build step must expose validated checkpoint availability"
)

restore_index = steps.index(restore)
installation_index = steps.index(installation)
checkpoint_restore_index = steps.index(checkpoint_restore)
build_index = steps.index(build)
save_index = steps.index(save)
checkpoint_save_index = steps.index(checkpoint_save)
materialization_index = steps.index(materialization)
assert(restore_index < installation_index, "compiler cache must restore before installation admission")
assert(
  installation_index < checkpoint_restore_index,
  "installation cache must precede source-build checkpoint restore"
)
assert(
  checkpoint_restore_index < build_index,
  "source-build checkpoint must restore before the build"
)
assert(save_index == build_index + 1, "compiler cache must save immediately after the build attempt")
assert(
  checkpoint_save_index == save_index + 1,
  "source-build checkpoint save must follow compiler-cache preservation"
)
assert(
  checkpoint_save_index < materialization_index,
  "all recovery cache evidence must precede materialization"
)

puts "source producer recovery-cache workflow policy: ok"
RUBY
