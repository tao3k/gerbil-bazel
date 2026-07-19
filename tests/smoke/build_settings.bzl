def _dependency_state_impl(_ctx):
    return []

dependency_state_flag = rule(
    implementation = _dependency_state_impl,
    build_setting = config.string(flag = True),
)
