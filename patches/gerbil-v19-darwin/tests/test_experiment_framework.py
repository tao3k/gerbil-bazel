import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from experiment_framework.context import Toolchain, data_path
from experiment_framework.process import execute, record
from experiment_framework.xml_evidence import XmlTable
from progressive_performance_gate import Limits


def test_debug_sidecar_text_identity_and_bounds(tmp_path):
    import struct
    from experiment_framework.compiler import text_identity
    image = bytearray(196)
    struct.pack_into('<8I', image, 0, 0xFEEDFACF, 0x100000C, 0, 1, 1, 152, 0, 0)
    struct.pack_into('<II', image, 32, 0x19, 152)
    struct.pack_into('<I', image, 96, 1)
    image[104:110] = b'__text'
    image[120:126] = b'__TEXT'
    struct.pack_into('<Q', image, 144, 4)
    struct.pack_into('<I', image, 152, 184)
    struct.pack_into('<II', image, 160, 188, 1)
    image[184:188] = b'\xc0\x03\x5f\xd6'
    original = tmp_path / 'original.o'
    original.write_bytes(image)
    first = text_identity(original)
    assert first['textBytes'] == 4 and first['relocations'] == 1
    image[184] ^= 1
    original.write_bytes(image)
    assert text_identity(original)['textSha256'] != first['textSha256']
    image[188] ^= 1
    original.write_bytes(image)
    assert text_identity(original)['relocationSha256'] != first['relocationSha256']
    original.write_bytes(image[:-1])
    with pytest.raises(ValueError, match='complete nonempty text'):
        text_identity(original)


def test_source_line_diagnostic_is_opt_in(tmp_path):
    from experiment_framework.compiler import diagnostic_environment
    default = diagnostic_environment({}, tmp_path, tmp_path / 'a.c', tmp_path)
    debug = diagnostic_environment({}, tmp_path, tmp_path / 'a.c', tmp_path, True)
    assert '-g1' not in default['BUILD_OBJ_CC_OPTIONS_PARAM']
    assert debug['BUILD_OBJ_CC_OPTIONS_PARAM'] == default['BUILD_OBJ_CC_OPTIONS_PARAM'] + ' -g1'


def test_debug_relocation_symbol_renumbering_is_not_target_substitution(tmp_path):
    import struct
    from experiment_framework.compiler import text_identity
    image = bytearray(261)
    struct.pack_into('<8I', image, 0, 0xFEEDFACF, 0x100000C, 0, 1, 2, 176, 0, 0)
    struct.pack_into('<II', image, 32, 0x19, 152)
    struct.pack_into('<I', image, 96, 1)
    image[104:110] = b'__text'
    image[120:126] = b'__TEXT'
    struct.pack_into('<Q', image, 144, 4)
    struct.pack_into('<I', image, 152, 208)
    struct.pack_into('<II', image, 160, 212, 1)
    struct.pack_into('<6I', image, 184, 2, 24, 220, 2, 252, 9)
    image[208:212] = b'\xc0\x03\x5f\xd6'
    struct.pack_into('<II', image, 212, 0, 1 << 27)
    struct.pack_into('<IBBHQ', image, 220, 1, 1, 0, 0, 0)
    struct.pack_into('<IBBHQ', image, 236, 5, 1, 0, 0, 0)
    image[252:] = b'\0one\0two\0'
    path = tmp_path / 'relocation.o'
    path.write_bytes(image)
    original = text_identity(path)
    struct.pack_into('<I', image, 220, 5)
    struct.pack_into('<I', image, 236, 1)
    struct.pack_into('<I', image, 216, (1 << 27) | 1)
    path.write_bytes(image)
    renumbered = text_identity(path)
    assert renumbered['relocationSha256'] != original['relocationSha256']
    assert renumbered['canonicalRelocationSha256'] == original['canonicalRelocationSha256']
    struct.pack_into('<I', image, 216, 1 << 27)
    path.write_bytes(image)
    assert text_identity(path)['canonicalRelocationSha256'] != original['canonicalRelocationSha256']


def test_persistent_fresh_output_and_symlink_escape(tmp_path):
    data = tmp_path / '.data'
    data.mkdir()
    assert data_path(tmp_path, data / 'new', fresh=True) == data / 'new'
    with pytest.raises(ValueError):
        data_path(tmp_path, data, fresh=True)
    (data / 'escape').symlink_to(tmp_path)
    with pytest.raises(ValueError):
        data_path(tmp_path, data / 'escape/out')


def test_canonical_home_and_selected_commands_are_separate(tmp_path):
    toolchain = Toolchain(tmp_path / 'binary', tmp_path / 'canonical')
    original = {'PATH': '/usr/bin', 'GAMBIT_DARWIN_TEST': '1',
                'GERBIL_MCP_TEST': '1', 'GERBIL_BUILD_PREFIX': 'wrong'}
    env = toolchain.environment(original, package_home=tmp_path / 'empty',
                                load_paths=[tmp_path / 'objects', toolchain.home / 'lib'],
                                workers=12, bin_dir=tmp_path / 'commands')
    assert env['GERBIL_HOME'] == str(toolchain.home)
    assert env['GERBIL_GSC'] == str(tmp_path / 'commands/gsc')
    assert env['GERBIL_BUILD_CORES'] == '12'
    assert env['GAMBOPT'].startswith(f'~~bin={tmp_path}/commands,~~lib={toolchain.home}/lib,')
    assert 'GERBIL_BUILD_PREFIX' not in env
    assert 'GAMBIT_DARWIN_TEST' not in env
    assert 'GERBIL_MCP_TEST' not in env
    assert original['GERBIL_BUILD_PREFIX'] == 'wrong'


def test_deadline_denies_and_reaps_owned_process(tmp_path):
    row = execute([sys.executable, '-c', 'import time;time.sleep(10)'],
                  tmp_path, os.environ, tmp_path / 'log', Limits('test', complete=1, first=0.05))
    assert not row['passed']
    assert row['performanceStop']['decision'] == 'DENY'
    assert row['cleanup']['reaped']
    assert row['cleanup']['terminalExitCode'] is not None


def test_recorder_timeout_reaps_without_turning_timeout_into_success(tmp_path, monkeypatch):
    import experiment_framework.process as process
    real = subprocess.Popen
    children = []

    def tracked(*args, **kwargs):
        child = real(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(process.subprocess, 'Popen', tracked)
    with pytest.raises(subprocess.TimeoutExpired):
        record([sys.executable, '-c', 'import time;time.sleep(10)'], tmp_path,
               os.environ, tmp_path / 'record.log', timeout=0.05, termination_grace=0.1)
    assert len(children) == 1
    assert children[0].poll() is not None


def test_deadline_kills_group_even_after_parent_exit(tmp_path, monkeypatch):
    import experiment_framework.process as process
    killpg = os.killpg
    popen = process.subprocess.Popen
    signals = []

    def tracked(pid, sig):
        signals.append((pid, sig))
        return killpg(pid, sig)

    monkeypatch.setattr(process.os, 'killpg', tracked)
    def exited_parent(*args, **kwargs):
        child = popen(*args, **kwargs)
        # Establish the scenario; descendant-held stdout stays open after exit.
        assert child.wait(timeout=2) == 0
        return child

    monkeypatch.setattr(process.subprocess, 'Popen', exited_parent)
    program = ('import subprocess,sys;'
               'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(10)"]);'
               'print(p.pid,flush=True)')
    row = execute([sys.executable, '-c', program], tmp_path, os.environ,
                  tmp_path / 'group.log', Limits('group', complete=0.3, first=None))
    assert not row['passed']
    assert row['cleanup']['terminalExitCode'] == 0
    assert row['cleanup']['reaped']
    assert any(sig == signal.SIGKILL for _, sig in signals)


def test_xml_references_are_checked():
    tree = ET.fromstring('<root><node><schema><col><mnemonic>x</mnemonic></col></schema>'
                         '<row><number id="one">1</number></row>'
                         '<row><number ref="one"/></row></node></root>')
    table = XmlTable(tree, ['x'])
    assert [fields[0].text for fields in table.rows()] == ['1', '1']
    tree.findall('./node/row')[1][0].set('ref', 'missing')
    with pytest.raises(ValueError, match='missing XML reference'):
        list(XmlTable(tree, ['x']).rows())
    tree.findall('./node/row')[1][0].set('id', 'one')
    with pytest.raises(ValueError, match='duplicate XML identifier'):
        XmlTable(tree, ['x'])


def test_unified_cli_dispatches_without_starting_workload():
    cli = Path(__file__).with_name('experiment.py')
    for name in ('stdlib', 'artifacts', 'counters', 'counter-summary', 'counter-stacks',
                 'compiler-frame', 'runtime-io', 'spawn-semantics', 'relink', 'retained', 'three-lines', 'atomic', 'resources'):
        result = subprocess.run([sys.executable, str(cli), name, '--help'],
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert '--output' in result.stdout or '--profile' in result.stdout


def test_allocation_census_excludes_other_compiler_transformations():
    cli = Path(__file__).with_name('experiment.py')
    required = ['--source', 'unused.c', '--reference-object', 'unused.o',
                '--home', 'unused-home', '--output', 'unused-output']
    for option in ('--source-lines', '--shared-parameter-result'):
        result = subprocess.run([sys.executable, str(cli), 'compiler-frame',
                                 '--allocation-sites', option, *required],
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == 2
        assert 'allocation census excludes other source transformations' in result.stderr


def test_process_census_requires_actual_root_observer(tmp_path):
    from experiment_framework.process import spawn_events
    trace = tmp_path / '7.log'
    with pytest.raises(ValueError, match='actual target'):
        spawn_events(tmp_path, 7)
    trace.write_text('1\t1\tgxi\tloaded\t-\t0\t0\t0\t0\n'
                     '2\t2.25\tgxi\tfork\t-\t0\t0\t0\t8\n')
    result = spawn_events(tmp_path, 7)
    assert result['apiCounts'] == {'fork': 1}
    assert result['summedApiSeconds'] == {'fork': 0.25}
    assert not result['completeDescendantCoverage']
    with pytest.raises(ValueError, match='actual target'):
        spawn_events(tmp_path, 8)
    trace.write_text('malformed\n')
    with pytest.raises(ValueError, match='complete process'):
        spawn_events(tmp_path, 7)


def test_compiler_diagnostics_preserve_base_flags_and_original_source(tmp_path):
    from experiment_framework.compiler import diagnostic_environment
    base = {'CORCXXFLAGS_GAMBUILD': 'original', 'PATH': 'original', 'CC': 'gcc'}
    home, source, output = tmp_path / 'home', tmp_path / 'original.c', tmp_path / 'output'
    env = diagnostic_environment(base, home, source, output)
    assert all(env[key] == value for key, value in base.items())
    assert env['BUILD_OBJ_INPUT_FILENAMES_PARAM'] == str(source)
    assert env['BUILD_OBJ_META_INFO_FILE_PARAM'] == str(source)
    assert env['BUILD_OBJ_CC_OPTIONS_PARAM'].split() == [
        '-O1', '-fstack-usage', '-fdump-rtl-expand', '-fdump-rtl-pro_and_epilogue']
    assert 'BUILD_OBJ_CC_PARAM' not in env


def test_runtime_candidate_compiles_without_diagnostic_dumps(tmp_path):
    from experiment_framework.compiler import diagnostic_environment
    base = {'CC': 'gcc', 'CORCXXFLAGS_GAMBUILD': 'original'}
    env = diagnostic_environment(base, tmp_path, tmp_path / 'carrier.c',
                                 tmp_path, frame_dumps=False)
    assert env['BUILD_OBJ_CC_OPTIONS_PARAM'] == '-O1'
    assert all(env[key] == value for key, value in base.items())


def test_shared_parameter_result_is_activation_local_and_retains_guard():
    from gambit_parameter_entry import PREAMBLE, share_result_storage
    original = (PREAMBLE + '\n#define ___MH_PROC gb_coalesced_host\n___BEGIN_M_COD\n'
                '  GB_PARAMETER_TRY(value)\n___END_M_COD\n')
    result = share_result_storage(original)
    assert result.count('struct gb_parameter_result gb_answer;') == 1
    assert '#ifdef GB_SHARED_PARAMETER_RESULT\nstruct gb_parameter_result gb_answer;' in result
    assert result.index('#define GB_SHARED_PARAMETER_RESULT 1') > result.index('#if defined(__APPLE__)')
    assert 'static struct gb_parameter_result gb_answer' not in result
    assert 'gb_parameter_lookup(___ps,(expression),&gb_answer)' in result
    with pytest.raises(ValueError, match='common host'):
        share_result_storage(original + 'GB_PARAMETER_TRY(other)\n')


def test_existing_raw_evidence_retains_exact_statistics():
    from correlate_stdlib_counter_stacks import correlate
    from summarize_native_cpu_profile import macho_functions
    from summarize_stdlib_counter_profile import precise_metric_groups, summarize
    root = Path(__file__).resolve().parents[3]
    profile = root / '.data/d1510-stdlib-counter-profile-v1'
    if not (profile / 'stack-correlation.json').exists():
        pytest.skip('private original trace is not available in this checkout')
    receipt = json.loads((profile / 'report.json').read_text())
    tree = ET.parse(profile / 'metrics-process.xml').getroot()
    expected = json.loads((profile / 'metric-summary.json').read_text())
    result = summarize(tree, receipt['targetPid'])
    assert result == {key: expected[key] for key in result}
    groups, _ = precise_metric_groups(tree, receipt['targetPid'])
    native = macho_functions(root / '.data/d1510-reader-whitespace-native-v2/gerbil')
    assert native['sha256'] == receipt['binarySha256']
    result = correlate(ET.parse(profile / 'time-profile.xml').getroot(),
                       receipt['targetPid'], native, groups)
    expected = json.loads((profile / 'stack-correlation.json').read_text())
    assert result == {key: expected[key] for key in result}
