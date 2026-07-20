def _scenario_state_impl(_ctx):
    return []

scenario_state_flag = rule(
    implementation = _scenario_state_impl,
    build_setting = config.string(flag = True),
)
