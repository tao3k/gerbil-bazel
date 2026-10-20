import pytest

from experiment_framework.native_receipt import read_native_receipt, read_native_suite_receipt


def fixture(tmp_path, status='0', marker='OK\n'):
    directory = tmp_path / 'run'
    directory.mkdir()
    (directory / 'exit-status.txt').write_text(status)
    (directory / 'time.txt').write_text('real 2.00\nuser 1.00\nsys 0.10\n')
    (directory / 'output.log').write_text(
        'NATIVE-ENTRY-CACHE-MISS\nCASE-OK real case\n'
        'interleaved GAMBIT-STATIC-OBJECT-HIT\n'
        'interleaved invoke (/isolated/gsc -obj module.c)\n' + marker)
    return directory


def test_interleaved_compile_events_are_counted(tmp_path):
    record = read_native_receipt(tmp_path, fixture(tmp_path), 1)
    assert record['correctnessPassed']
    assert record['objectCalls'] == record['staticObjectHits'] == 1
    assert record['entryCacheMiss'] and not record['entryCacheHit']


def test_closed_link_events_are_counted_without_inventing_object_calls(tmp_path):
    directory = fixture(tmp_path)
    with (directory / 'output.log').open('a') as stream:
        stream.write('invoke interleaved GAMBIT-GENERATED-C-MISS\n'
                     'GAMBIT-GENERATED-C-HIT\nGAMBIT-GENERATED-C-UNCACHEABLE\n'
                     'interleaved GAMBIT-CLOSED-LINK-SELECTED 224\n')
    record = read_native_receipt(tmp_path, directory, 1)
    assert record['generatedCHits'] == record['generatedCMisses'] == record['generatedCUncacheable'] == 1
    assert record['closedLinkSelections'] == [224]
    assert record['objectCalls'] == 1


@pytest.mark.parametrize('status,marker', [('70', 'OK\n'), ('0', ''), ('0', 'HARNESS-OK\n')])
def test_no_success_without_exit_and_final_ok(tmp_path, status, marker):
    assert not read_native_receipt(tmp_path, fixture(tmp_path, status, marker), 1)['correctnessPassed']


def test_inventory_is_required(tmp_path):
    assert not read_native_receipt(tmp_path, fixture(tmp_path), 2)['correctnessPassed']


@pytest.mark.parametrize('passes,plan,correct', [
    (['one', 'two'], 'parallel=1 exclusive=1 jobs=12', True),
    (['one'], 'parallel=1 exclusive=1 jobs=12', False),
    (['one', 'one'], 'parallel=1 exclusive=1 jobs=12', False),
    (['one', 'two'], 'parallel=1 exclusive=0 jobs=12', False),
])
def test_full_suite_needs_exact_module_coverage(tmp_path, passes, plan, correct):
    directory = fixture(tmp_path, marker='')
    with (directory / 'output.log').open('a') as stream:
        stream.write('[ascent-test] PLAN ' + plan + '\n')
        for module in passes:
            stream.write('NATIVE-MODULES-OK\nOK\n[ascent-test] PASS ' + module + '\n')
    record = read_native_suite_receipt(tmp_path, directory, ['one', 'two'])
    assert record['correctnessPassed'] is correct


def test_full_suite_allows_nested_native_control_markers(tmp_path):
    directory = fixture(tmp_path, marker='')
    with (directory / 'output.log').open('a') as stream:
        stream.write('[ascent-test] PLAN parallel=1 exclusive=0 jobs=12\n'
                     'NATIVE-MODULES-OK\nNATIVE-MODULES-OK\nOK\n[ascent-test] PASS one\n')
    assert read_native_suite_receipt(tmp_path, directory, ['one'])['correctnessPassed']
