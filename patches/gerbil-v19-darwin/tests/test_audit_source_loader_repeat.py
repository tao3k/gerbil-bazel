from audit_source_loader_repeat import normalize, work


def test_normalizes_only_project_location(tmp_path):
    project = tmp_path / 'project'
    value = {'path': f'{project}/.gerbil/lib', 'workers': '12', 'embedded': '0'}
    normalized = normalize(value, project)
    assert normalized['path'] == '<project>/.gerbil/lib'
    assert normalized['workers'] == '12' and normalized['embedded'] == '0'


def test_work_is_counted_not_ordered(tmp_path):
    lines = ['... compile util/compat', '... compile util/compat',
             '... execute compile job (compile-file x.scm)', 'diagnostic']
    (tmp_path / 'build.log').write_text('\n'.join(lines))
    counts = work(tmp_path)
    assert counts['... compile util/compat'] == 2
    assert sum(counts.values()) == 3
