import pytest
from pathlib import Path
import subprocess
import sys
from run_stdlib_import_cost import parse_phases, parse_calls, parse_binding_census, parse_budgets, parse_reader_budgets, parse_filesystem_budgets
from run_stdlib_import_cost import parse_length_budgets, parse_binding_budgets


@pytest.mark.parametrize('flags', [
    ['--source-module'],
    ['--source-module', '--module', ':std/make'],
    ['--length-budget', '--module', ':std/make'],
    ['--binding-budget', '--module', ':std/make'],
])
def test_diagnostic_mode_rejects_incomplete_configuration(tmp_path, flags):
    output = tmp_path / 'must-not-exist'
    result = subprocess.run([sys.executable, str(Path(__file__).with_name(
        'run_stdlib_import_cost.py')), '--output', str(output), *flags],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert not output.exists()
    assert 'requires' in result.stderr


def binding_transcript():
    return ('STDLIB-BINDING-BUDGET\timport\t2\t2\t2\t0.01\t0.02\t128\t64\n'
            + ''.join('STDLIB-BINDING-BUDGET\t' + phase + '\t0\t0\t0\t0.0\t0.0\t0.0\t0.0\n'
                      for phase in ('eval', 'cached-import', 'cached-eval'))
            + 'STDLIB-BINDING-RESTORED\n')


def test_binding_budget_requires_normal_entry_and_return():
    rows = parse_binding_budgets(binding_transcript())
    assert rows[0]['entryAllocationMetricDeltaBytes'] == 128
    assert rows[0]['returnSeconds'] == 0.02
    assert rows[1]['calls'] == 0
    assert rows[0]['allocationDeltaNonnegative'] is True
    negative = parse_binding_budgets(binding_transcript().replace('\t128\t', '\t-128\t'))[0]
    assert negative['entryAllocationMetricDeltaBytes'] == -128
    assert negative['allocationDeltaNonnegative'] is False


@pytest.mark.parametrize('text', [
    binding_transcript().replace('\t2\t2\t2', '\t2\t1\t2'),
    binding_transcript().replace('\t0.01', '\tnan'),
    binding_transcript().replace('\t128\t', '\t128.5\t'),
    binding_transcript().replace('STDLIB-BINDING-RESTORED\n', ''),
    binding_transcript().replace('cached-eval', 'eval'),
    binding_transcript().replace('\t0\t0\t0\t0.0', '\t0\t0\t0\t0.1', 1),
])
def test_incomplete_or_invalid_binding_budget_is_rejected(text):
    with pytest.raises(ValueError):
        parse_binding_budgets(text)


def length_transcript():
    return ('STDLIB-LENGTH-BUDGET\timport\t2\t7\t4\t0.01\n'
            'STDLIB-LENGTH-BUDGET\teval\t0\t0\t0\t0.0\n'
            'STDLIB-LENGTH-BUDGET\tcached-import\t0\t0\t0\t0.0\n'
            'STDLIB-LENGTH-BUDGET\tcached-eval\t0\t0\t0\t0.0\n'
            'STDLIB-LENGTH-RESTORED\n')


def test_length_budget_allows_explicit_zero_coverage():
    rows = parse_length_budgets(length_transcript())
    assert rows[0]['nodes'] == 7
    assert rows[1]['calls'] == 0


@pytest.mark.parametrize('text', [
    length_transcript().replace('STDLIB-LENGTH-RESTORED\n', ''),
    length_transcript().replace('\t0.01', '\tnan'),
    length_transcript().replace('\t2\t7\t4', '\t2\t9\t4'),
    length_transcript().replace('\t2\t7\t4', '\t2\t7\t8'),
    length_transcript().replace('\t0\t0\t0\t0.0', '\t0\t0\t0\t0.1', 1),
    length_transcript().replace('cached-eval', 'eval'),
])
def test_invalid_length_budget_is_rejected(text):
    with pytest.raises(ValueError):
        parse_length_budgets(text)


def test_filesystem_budget_requires_original_restore_and_non_nested_calls():
    text = ('STDLIB-FILESYSTEM-BUDGET\tfile-info\timport\t0\t0.01\t0.02\t1\t0\n'
            'STDLIB-FILESYSTEM-BUDGET\tnormalize-directory\timport\t0\t0.02\t0.03\t2\t0\n'
            'STDLIB-CALL\t1\tfilesystem\timport\tnot-classified\t0.1\tfile-info\n'
            'STDLIB-CALL\t1\tfilesystem\timport\tnot-classified\t0.1\tnormalize-directory\n'
            'STDLIB-CALL\t0\timport\timport\tno-exact-key\t0.3\t:std/a\n'
            'STDLIB-FILESYSTEM-RESTORED\n')
    calls = parse_calls(text)
    rows = parse_filesystem_budgets(text, calls)
    assert rows[0]['systemSeconds'] == 0.02
    assert rows[1]['minorFaults'] == 2
    for invalid in (text.replace('STDLIB-FILESYSTEM-RESTORED\n', ''),
                    text.replace('\t0.01\t', '\tnan\t'),
                    text.replace('\t1\t0\n', '\t1.5\t0\n'),
                    text.replace('\timport\t0\t', '\timport\t1\t', 1),
                    text.replace('\tfile-info\timport', '\tunknown\timport', 1)):
        with pytest.raises(ValueError):
            parse_filesystem_budgets(invalid, calls)
    with pytest.raises(ValueError):
        parse_filesystem_budgets(text, calls[:-2])


def test_reached_reader_budget_requires_restore_and_matching_calls():
    text = ('STDLIB-READ-BUDGET\t0\timport\t0.1\t0.2\t0.01\t1024\t"std/a.ssi"\n'
            'STDLIB-CALL\t1\tinterface-read\timport\tnot-classified\t0.3\t"std/a.ssi"\n'
            'STDLIB-CALL\t0\timport\timport\tno-exact-key\t0.4\t:std/a\n'
            'STDLIB-READER-RESTORED\n')
    calls = parse_calls(text)
    row = parse_reader_budgets(text, calls)[0]
    assert row['allocatedBytesDelta'] == 1024
    assert row['readDepth'] == 0
    negative = parse_reader_budgets(text.replace('\t1024\t', '\t-1024\t'), calls)[0]
    assert negative['allocatedBytesDelta'] == -1024
    assert negative['allocationDeltaNonnegative'] is False
    for invalid in (text.replace('STDLIB-READER-RESTORED\n', ''),
                    text.replace('\t0.1\t', '\tnan\t'),
                    text.replace('\t0.01\t', '\t1\t'),
                    text.replace('std/a.ssi', 'std/b.ssi', 1),
                    text.replace('STDLIB-READ-BUDGET\t0', 'STDLIB-READ-BUDGET\t-1')):
        with pytest.raises(ValueError):
            parse_reader_budgets(invalid, calls)


def budget_transcript(value='1'):
    values = [value, '0', '2', '0.25', '0', '0.3', '2', '1000', '1', '0',
              '10000', '2000', '1000', '800', '200']
    return '\n'.join('STDLIB-BUDGET\t' + phase + '\t' + '\t'.join(values)
                     for phase in ('import', 'eval', 'cached-import', 'cached-eval'))


def test_process_budget_separates_cpu_and_latest_gc_snapshot():
    row = parse_budgets(budget_transcript())[0]
    assert row['gcCpuFraction'] == 0.25
    assert row['latestGcInThisPhase'] is True
    assert row['allocatedBytesDelta'] == 1000
    text = budget_transcript().replace('\t2\t1000', '\t0\t1000')
    assert parse_budgets(text)[0]['latestGcInThisPhase'] is False


@pytest.mark.parametrize('text', ['', budget_transcript('nan'), budget_transcript('-1'),
                                budget_transcript('0'),
                                budget_transcript().replace('cached-eval', 'eval'),
                                budget_transcript().replace('\t2\t1000', '\t2.5\t1000')])
def test_invalid_process_budget_is_rejected(text):
    with pytest.raises(ValueError):
        parse_budgets(text)


def transcript(value='0.01'):
    return '\n'.join('STDLIB-PHASE\t' + phase + '\t' + value for phase in
                     ('import', 'eval', 'cached-import', 'cached-eval')) + \
           '\nCONTEXT-IDENTITY-OK\nOK\n'


def test_four_completed_phases():
    assert len(parse_phases(transcript())) == 4


@pytest.mark.parametrize('text', [transcript('nan'), transcript('-1'),
                                transcript().replace('cached-import', 'import'),
                                transcript().replace('CONTEXT-IDENTITY-OK\n', ''),
                                transcript() + '*** ERROR\n'])
def test_invalid_completion_is_rejected(text):
    with pytest.raises(ValueError):
        parse_phases(text)


def test_mixed_nested_calls_are_subtracted_once():
    rows = parse_calls('STDLIB-CALL\t1\teval\timport\tnot-classified\t0.2\tstd/test\n'
                       'STDLIB-CALL\t0\timport\timport\tno-exact-key\t0.5\t:std/test\n')
    assert [row['observedOwnSeconds'] for row in rows] == [0.2, 0.3]


@pytest.mark.parametrize('text', ['',
    'STDLIB-CALL\t1\teval\timport\tnot-classified\t0.2\tstd/test\n',
    'STDLIB-CALL\t0\teval\timport\tnot-classified\tnan\tstd/test\n'])
def test_incomplete_trace_is_rejected(text):
    with pytest.raises(ValueError):
        parse_calls(text)


def test_gambit_prepare_and_run_are_joint_children():
    rows = parse_calls('STDLIB-CALL\t1\tgambit-prepare\timport\tnot-classified\t0.3\tbegin\n'
                       'STDLIB-CALL\t1\tgambit-run\timport\tnot-classified\t0.5\tbegin\n'
                       'STDLIB-CALL\t0\tscheme-eval\timport\tnot-classified\t1.0\tbegin\n')
    assert rows[-1]['observedOwnSeconds'] == pytest.approx(0.2)


def test_interface_expansion_subtracts_nested_eval_and_import_once():
    rows = parse_calls(
        'STDLIB-CALL\t2\tscheme-eval\timport\tnot-classified\t0.2\tbegin\n'
        'STDLIB-CALL\t1\tinterface-expand\timport\tnot-classified\t0.5\t(%#begin-syntax std/io 0)\n'
        'STDLIB-CALL\t1\timport\timport\tno-exact-key\t0.1\t:std/error\n'
        'STDLIB-CALL\t0\timport\timport\tno-exact-key\t1.0\t:std/io\n')
    assert [row['observedOwnSeconds'] for row in rows] == pytest.approx([0.2, 0.3, 0.1, 0.4])


def test_interface_expansion_rejects_impossible_child_interval():
    with pytest.raises(ValueError, match='child intervals exceed parent'):
        parse_calls(
            'STDLIB-CALL\t1\tscheme-eval\timport\tnot-classified\t0.6\tbegin\n'
            'STDLIB-CALL\t0\tinterface-expand\timport\tnot-classified\t0.5\t(%#begin-syntax std/io 0)\n')


def test_binding_census_distinguishes_attempts_from_retained_objects():
    assert parse_binding_census('STDLIB-IMPORT-BINDINGS\tstd/io\t10\t5\t3\t4\n') == [
        dict(context='std/io', attempts=10, retainedPriorBinding=5,
             strongRetainedPriorBinding=3, intraFormRepeatedKeys=4)]


@pytest.mark.parametrize('line', ['',
    'STDLIB-IMPORT-BINDINGS\tstd/io\t1\t2\t0\t0\n',
    'STDLIB-IMPORT-BINDINGS\tstd/io\t5\t3\t4\t0\n',
    'STDLIB-IMPORT-BINDINGS\tstd/io\t5\t0\t0\t6\n',
    'STDLIB-IMPORT-BINDINGS\tstd/io\t0\t0\t0\t0\n'])
def test_binding_census_rejects_invalid_or_unreached_counts(line):
    with pytest.raises(ValueError):
        parse_binding_census(line)
