import xml.etree.ElementTree as ET

import pytest

from summarize_stdlib_counter_profile import COLUMNS, summarize


def test_recorder_budget_uses_one_shared_deadline(monkeypatch):
    import run_stdlib_counter_profile as recorder
    monkeypatch.setattr(recorder.time, 'monotonic', lambda: 12)
    assert recorder.remaining_budget(10, 30) == 28
    monkeypatch.setattr(recorder.time, 'monotonic', lambda: 40)
    with pytest.raises(TimeoutError, match='whole diagnostic budget'):
        recorder.remaining_budget(10, 30)


def fixture(pid=7):
    root = ET.Element('trace-query-result')
    node = ET.SubElement(root, 'node')
    schema = ET.SubElement(node, 'schema')
    for name in COLUMNS:
        ET.SubElement(ET.SubElement(schema, 'col'), 'mnemonic').text = name
    for precise in ('0', '1'):
        for name, value in [('processing', 60), ('discarded', 5),
                            ('delivery', 30), ('useful', 5), ('cycle', 100)]:
            row = ET.SubElement(node, 'row')
            ET.SubElement(row, 'start-time').text = '100'
            ET.SubElement(row, 'duration').text = '10'
            ET.SubElement(ET.SubElement(row, 'process'), 'pid').text = str(pid)
            ET.SubElement(row, 'uint64').text = str(value if name == 'cycle' else 0)
            ET.SubElement(row, 'fixed-decimal').text = str(value)
            ET.SubElement(row, 'string').text = name
            ET.SubElement(row, 'boolean').text = precise
    return root


def test_overlapping_coarse_rows_are_not_double_counted():
    result = summarize(fixture(), 7)
    assert result['recordedCycles'] == 100
    assert result['coarseRowsExcluded'] == 5
    assert result['cycleWeightedNormalizedMetricShares']['processing'] == 0.6
    assert not result['performanceQualified']


def test_wrong_pid_rejected():
    with pytest.raises(ValueError, match='different process'):
        summarize(fixture(pid=8), 7)


def test_duplicate_metric_rejected():
    tree = fixture()
    tree.find('node').append(tree.findall('./node/row')[5])
    with pytest.raises(ValueError, match='duplicate interval metric'):
        summarize(tree, 7)


def test_negative_metric_rejected():
    tree = fixture()
    tree.findall('./node/row')[5].find('fixed-decimal').text = '-1'
    with pytest.raises(ValueError, match='invalid named metric'):
        summarize(tree, 7)


def context_fixture():
    root = ET.Element('trace-query-result')
    node = ET.SubElement(root, 'node')
    schema = ET.SubElement(node, 'schema')
    columns = ['time', 'thread', 'process', 'core', 'thread-state', 'weight', 'stack']
    for name in columns:
        ET.SubElement(ET.SubElement(schema, 'col'), 'mnemonic').text = name
    for index, kind in enumerate(('P', 'E')):
        row = ET.SubElement(node, 'row')
        ET.SubElement(row, 'time').text = str(11 + index)
        ET.SubElement(row, 'thread')
        ET.SubElement(ET.SubElement(row, 'process'), 'pid').text = '7'
        ET.SubElement(row, 'core', fmt=f'CPU {index} ({kind} Core)').text = str(index)
        ET.SubElement(row, 'thread-state').text = 'Running'
        ET.SubElement(row, 'weight').text = str(100 * (index + 1))
        stack = ET.SubElement(ET.SubElement(row, 'stack'), 'backtrace')
        for frame_index in range(index + 1):
            frame = ET.SubElement(stack, 'frame', name=f'function{frame_index}')
            ET.SubElement(frame, 'binary', name='external', UUID='other')
    return root


def test_core_context_preserves_correlation_and_separates_coverage():
    from correlate_stdlib_counter_stacks import correlate
    from summarize_stdlib_counter_profile import CATEGORIES
    tree = context_fixture()
    groups = {(10, 10): {name: 1 for name in CATEGORIES}}
    original = correlate(tree, 7, {'uuid': 'retained'}, groups)
    result = correlate(tree, 7, {'uuid': 'retained'}, groups, include_context=True)
    assert {key: result[key] for key in original} == original
    assert result['coreContext']['P']['stackDepthSamples'] == {'1': 1}
    assert result['coreContext']['E']['stackDepthSamples'] == {'2': 1}
    assert result['coreContext']['E']['sampleWeightNanoseconds'] == 200
    assert not result['coreCycleAttribution']
    assert not result['schedulerCauseEstablished']


@pytest.mark.parametrize('label', ['CPU 99 (P Core)', 'CPU 0', 'CPU 0 (Unknown Core)'])
def test_core_context_rejects_missing_or_conflicting_core_identity(label):
    from correlate_stdlib_counter_stacks import correlate
    from summarize_stdlib_counter_profile import CATEGORIES
    tree = context_fixture()
    tree.find('./node/row/core').set('fmt', label)
    groups = {(10, 10): {name: 1 for name in CATEGORIES}}
    with pytest.raises(ValueError, match='core identity'):
        correlate(tree, 7, {'uuid': 'retained'}, groups, include_context=True)


def test_layout_keeps_same_name_functions_separate_and_models_translation_only():
    from correlate_stdlib_counter_stacks import layout_geometry
    native = dict(starts=[0, 40], textEnd=80, names={0: {'same'}, 40: {'same'}})
    result = layout_geometry(native, {(0, 12): 100, (0, 16): 100, (40, 44): 100}, 16)
    assert len(result['functions']) == 2
    first = result['functions'][0]
    assert first['observedSampledPages'] == 2
    assert first['unconstrainedTranslationLowerBoundPages'] == 1
    assert first['maximumWithinFunctionSampledPageReduction'] == 1
    assert not result['pageFaultAttribution']
    assert not result['functionEntryOrderRecorded']
    assert not result['performanceQualified']


@pytest.mark.parametrize('page_size', [0, 3, 12, True])
def test_layout_rejects_invalid_page_size(page_size):
    from correlate_stdlib_counter_stacks import layout_geometry
    with pytest.raises(ValueError, match='page size'):
        layout_geometry({}, {}, page_size)


def test_layout_rejects_wrong_extent_or_unaligned_sample():
    from correlate_stdlib_counter_stacks import layout_geometry
    native = dict(starts=[0, 16], textEnd=32, names={})
    with pytest.raises(ValueError, match='function extent'):
        layout_geometry(native, {(0, 20): 1}, 16)
    with pytest.raises(ValueError, match='aligned'):
        layout_geometry(native, {(0, 3): 1}, 16)


def test_layout_requires_actual_native_samples():
    from correlate_stdlib_counter_stacks import layout_geometry
    with pytest.raises(ValueError, match='native sample sites'):
        layout_geometry({}, {}, 16)


def native_context_fixture():
    tree = context_fixture()
    for row in tree.findall('./node/row'):
        for frame in row.findall('./stack/backtrace/frame'):
            frame.set('name', 'actual')
            frame.set('addr', '0xc')
            frame.find('binary').set('UUID', 'retained')
            frame.find('binary').set('load-addr', '0x0')
    return tree


def test_native_sites_without_layout_preserve_old_statistics():
    from correlate_stdlib_counter_stacks import correlate
    from summarize_stdlib_counter_profile import CATEGORIES
    tree = native_context_fixture()
    native = dict(uuid='retained', textBase=0, textStart=0, textEnd=32,
                  starts=[0], names={0: {'actual'}}, executableSections=[])
    groups = {(10, 10): {name: 1 for name in CATEGORIES}}
    original = correlate(tree, 7, native, groups)
    result = correlate(tree, 7, native, groups, include_sites=True)
    assert {key: result[key] for key in original} == original
    assert result['nativeSites'] == [dict(functionStart='0x0', nativePc='0xc',
                                         sampleWeightNanoseconds=300)]


def test_layout_preserves_old_statistics_and_normalizes_actual_pc_alignment():
    from correlate_stdlib_counter_stacks import correlate
    from summarize_stdlib_counter_profile import CATEGORIES
    tree = native_context_fixture()
    native = dict(uuid='retained', textBase=0, textStart=0, textEnd=32,
                  starts=[0], names={0: {'actual'}}, executableSections=[])
    tree.find('./node/row/stack/backtrace/frame').set('addr', '0xd')
    groups = {(10, 10): {name: 1 for name in CATEGORIES}}
    original = correlate(tree, 7, native, groups)
    result = correlate(tree, 7, native, groups, page_size=16)
    assert {key: result[key] for key in original} == original
    assert result['nativePageGeometry']['functions'][0]['distinctSampledPCs'] == 1
    assert result['nativePageGeometry']['functions'][0]['sampleWeightNanoseconds'] == 300
    tree.find('./node/row/stack/backtrace/frame/binary').set('load-addr', '0x4')
    with pytest.raises(ValueError, match='image page alignment'):
        correlate(tree, 7, native, groups, page_size=16)
