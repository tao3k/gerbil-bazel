"""Stable public API for Gerbil Bazel consumers."""

load(
    ":project.bzl",
    _GerbilProjectInfo = "GerbilProjectInfo",
    _gerbil_project_compile_rule = "gerbil_project_compile",
    _gerbil_project_dev = "gerbil_project_dev",
    _gerbil_project_test = "gerbil_project_test",
)
load(
    ":toolchain.bzl",
    _GERBIL_TOOLCHAIN_TYPE = "GERBIL_TOOLCHAIN_TYPE",
    _GerbilToolchainInfo = "GerbilToolchainInfo",
    _resolved_gerbil_toolchain = "resolved_gerbil_toolchain",
)

GERBIL_TOOLCHAIN_TYPE = _GERBIL_TOOLCHAIN_TYPE
GerbilProjectInfo = _GerbilProjectInfo
GerbilToolchainInfo = _GerbilToolchainInfo
gerbil_project_dev = _gerbil_project_dev
gerbil_project_test = _gerbil_project_test
resolved_gerbil_toolchain = _resolved_gerbil_toolchain

def _non_negative(name, value):
    if type(value) != "int" or value < 0:
        fail("{} must be a non-negative integer, got {}".format(name, value))
    return value

def gerbil_project_execution_policy(
        timeout_seconds = 0,
        max_rss_bytes = 0,
        rss_headroom_bytes = 0,
        memory_per_core_bytes = 0,
        sample_milliseconds = 0):
    """Declares adaptive execution supervision for a Gerbil project action.

    Zero requests the Scheme guard's host-adaptive memory ceiling. The guard
    derives the action budget from live available memory and preserves host
    headroom, so the same declaration is valid on small and large workers.
    Zero core values remain adaptive and never encode a fixed machine profile.
    """
    return struct(
        memory_per_core_bytes = _non_negative(
            "memory_per_core_bytes",
            memory_per_core_bytes,
        ),
        max_rss_bytes = _non_negative("max_rss_bytes", max_rss_bytes),
        rss_headroom_bytes = _non_negative(
            "rss_headroom_bytes",
            rss_headroom_bytes,
        ),
        sample_milliseconds = _non_negative(
            "sample_milliseconds",
            sample_milliseconds,
        ),
        timeout_seconds = _non_negative("timeout_seconds", timeout_seconds),
    )

def gerbil_project_compile(
        name,
        execution_policy = None,
        **kwargs):
    """Builds a Gerbil project under adaptive supervision by default.

    Existing explicit process_guard attributes remain authoritative. When no
    legacy guard attribute is present, the public API installs the adaptive
    default policy.
    """
    if execution_policy == None:
        if "process_guard" in kwargs:
            _gerbil_project_compile_rule(name = name, **kwargs)
            return
        execution_policy = gerbil_project_execution_policy()

    legacy_guard_attributes = [
        "process_guard",
        "process_guard_max_rss_bytes",
        "process_guard_memory_per_core_bytes",
        "process_guard_rss_headroom_bytes",
        "process_guard_sample_milliseconds",
        "process_guard_timeout_seconds",
    ]
    for attribute in legacy_guard_attributes:
        if attribute in kwargs:
            fail("{} cannot be combined with execution_policy".format(attribute))

    _gerbil_project_compile_rule(
        name = name,
        process_guard = True,
        process_guard_max_rss_bytes = str(execution_policy.max_rss_bytes),
        process_guard_memory_per_core_bytes = str(execution_policy.memory_per_core_bytes),
        process_guard_rss_headroom_bytes = str(execution_policy.rss_headroom_bytes),
        process_guard_sample_milliseconds = execution_policy.sample_milliseconds,
        process_guard_timeout_seconds = execution_policy.timeout_seconds,
        **kwargs
    )
