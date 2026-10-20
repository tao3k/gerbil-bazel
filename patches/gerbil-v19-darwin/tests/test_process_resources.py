import ctypes
import os
import sys
import pytest

from experiment_framework.resources import FIELDS, UsageV4, decode, DarwinUsage, DarwinGroupUsage
from experiment_framework.process import execute
from progressive_performance_gate import Limits


def test_reader_budget_requires_complete_inventory(tmp_path):
    import json
    from experiment_framework.resources import reader_result
    source = (tmp_path / 'source.ss').resolve()
    log = tmp_path / 'log'
    log.write_text('READ-BUDGET\t' + json.dumps(str(source)) + '\t0.2\t0.1\t0.01\t3\n')
    result = reader_result(log, [source])
    assert result['files'] == 1 and result['topLevelForms'] == 3
    assert result['readCpuSeconds'] == pytest.approx(.11)
    with pytest.raises(ValueError, match='complete selected'):
        reader_result(log, [source, tmp_path / 'missing.ss'])
    log.write_text(log.read_text() * 2)
    with pytest.raises(ValueError, match='one reader row'):
        reader_result(log, [source])


@pytest.mark.parametrize('metric', ['nan', 'inf', '-1'])
def test_reader_budget_rejects_invalid_times(tmp_path, metric):
    import json
    from experiment_framework.resources import reader_result
    source = (tmp_path / 'source.ss').resolve()
    log = tmp_path / 'log'
    log.write_text('READ-BUDGET\t' + json.dumps(str(source)) + '\t' + metric + '\t0\t0\t0\n')
    with pytest.raises(ValueError, match='finite nonnegative'):
        reader_result(log, [source])


def test_sdk_v4_layout():
    assert len(FIELDS) == 35
    assert ctypes.sizeof(UsageV4) == 296
    assert UsageV4.user_time.offset == 16
    assert UsageV4.runnable_time.offset == 288


def test_mach_units_and_independent_counters():
    usage = UsageV4(user_time=24_000_000, system_time=12_000_000,
                    runnable_time=72_000_000, child_user_time=6_000_000,
                    instructions=123, pageins=9, proc_start_abstime=7)
    row = decode(usage, 125, 3)
    assert row['userSeconds'] == pytest.approx(1)
    assert row['systemSeconds'] == pytest.approx(.5)
    assert row['runnableSeconds'] == pytest.approx(3)
    assert row['reapedChildUserSeconds'] == pytest.approx(.25)
    assert row['pidStartMachTicks'] == 7
    assert row['instructions'] == 123 and row['pageins'] == 9
    assert 'waitSeconds' not in row


@pytest.mark.parametrize('numer,denom', [(0, 1), (1, 0), (-1, 1)])
def test_bad_timebase(numer, denom):
    with pytest.raises(ValueError):
        decode(UsageV4(), numer, denom)


def test_optional_observation_does_not_fake_first_output(tmp_path):
    pids = []
    def read(pid):
        pids.append(pid)
        return dict(instructions=1)
    row = execute([sys.executable, '-c', 'import time;time.sleep(10)'],
                  tmp_path, os.environ, tmp_path / 'log',
                  Limits('resource-test', complete=1, first=.1), resource_reader=read)
    assert pids and row['resourceSamples'][0]['pid'] == pids[0]
    assert not row['passed'] and not row['performanceQualified']
    assert row['performanceStop']['reason'] == 'first-real-log-deadline'
    assert row['cleanup']['reaped']
    assert (tmp_path / 'log').read_bytes() == b''


def test_observation_error_keeps_original_process_and_gate(tmp_path):
    def read(pid):
        raise OSError('unavailable')
    row = execute([sys.executable, '-c', 'print("OK",flush=True)'],
                  tmp_path, os.environ, tmp_path / 'log',
                  Limits('resource-test', complete=2, first=1), resource_reader=read)
    assert row['passed'] and row['exitCode'] == 0
    assert row['resourceErrors'] and not row['resourceSamples']
    assert not row['performanceQualified']
    assert (tmp_path / 'log').read_text().strip() == 'OK'


def group_reader(monkeypatch, count=2):
    from types import SimpleNamespace
    def list_group(pid, buffer, extent):
        assert pid == 100 and extent == 256 * ctypes.sizeof(ctypes.c_int)
        buffer[0], buffer[1] = 100, 101
        return count
    def name(pid, buffer, extent):
        ctypes.memmove(buffer, b'gerbil\0', 7)
        return 6
    reader = DarwinGroupUsage.__new__(DarwinGroupUsage)
    reader.proc = SimpleNamespace(proc_listpgrppids=list_group, proc_name=name)
    monkeypatch.setattr('experiment_framework.resources.os.getpgid', lambda pid: 100)
    monkeypatch.setattr(DarwinUsage, '__call__', lambda self, pid: dict(instructions=pid))
    return reader


def test_group_uses_pid_count_not_byte_count(monkeypatch):
    row = group_reader(monkeypatch)(100)
    assert [process['pid'] for process in row['processes']] == [100, 101]
    assert row['observedMembers'] == 2 and not row['memberErrors']
    assert not row['completeDescendantCoverage']


@pytest.mark.parametrize('count', [0, 256, 1024])
def test_group_rejects_empty_or_possibly_truncated_inventory(monkeypatch, count):
    with pytest.raises(ValueError, match='untruncated'):
        group_reader(monkeypatch, count)(100)


def test_group_refuses_unowned_group(monkeypatch):
    with pytest.raises(ValueError, match='leader'):
        group_reader(monkeypatch)(101)
