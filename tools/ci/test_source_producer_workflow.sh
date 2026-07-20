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
build = step_named(steps, "Build Gerbil on Linux")
save = step_named(steps, "Save Linux compiler cache")
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

restore_index = steps.index(restore)
installation_index = steps.index(installation)
build_index = steps.index(build)
save_index = steps.index(save)
materialization_index = steps.index(materialization)
assert(restore_index < installation_index, "compiler cache must restore before installation admission")
assert(installation_index < build_index, "installation cache must gate the source build")
assert(save_index == build_index + 1, "compiler cache must save immediately after the build attempt")
assert(save_index < materialization_index, "compiler-cache evidence must precede materialization")

puts "source producer compiler-cache workflow policy: ok"
RUBY
