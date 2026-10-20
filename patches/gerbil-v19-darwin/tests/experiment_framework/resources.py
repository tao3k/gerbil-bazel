"""Read-only Darwin process counters; not full-tree or performance admission."""
import ctypes
import os
import sys


def reader_result(log, expected):
    import csv
    import json
    import math
    from pathlib import Path
    seen = set()
    wall = cpu = 0.0
    forms = 0
    with log.open(newline='') as stream:
        for fields in csv.reader(stream, delimiter='\t', quoting=csv.QUOTE_NONE):
            if len(fields) != 6 or fields[0] != 'READ-BUDGET':
                raise ValueError('exact native reader rows required')
            path = Path(json.loads(fields[1])).resolve()
            if path not in expected or path in seen:
                raise ValueError('one reader row per selected source required')
            times = [float(value) for value in fields[2:5]]
            count = int(fields[5])
            if any(not math.isfinite(value) or value < 0 for value in times) or count < 0:
                raise ValueError('finite nonnegative native reader metrics required')
            seen.add(path)
            wall += times[0]
            cpu += sum(times[1:])
            forms += count
    if seen != set(expected):
        raise ValueError('complete selected reader inventory required')
    return dict(files=len(seen), readWallSeconds=wall, readCpuSeconds=cpu,
                topLevelForms=forms)


FIELDS = '''user_time system_time pkg_idle_wkups interrupt_wkups pageins
wired_size resident_size phys_footprint proc_start_abstime proc_exit_abstime
child_user_time child_system_time child_pkg_idle_wkups child_interrupt_wkups
child_pageins child_elapsed_abstime diskio_bytesread diskio_byteswritten
cpu_time_qos_default cpu_time_qos_maintenance cpu_time_qos_background
cpu_time_qos_utility cpu_time_qos_legacy cpu_time_qos_user_initiated
cpu_time_qos_user_interactive billed_system_time serviced_system_time
logical_writes lifetime_max_phys_footprint instructions cycles billed_energy
serviced_energy interval_max_phys_footprint runnable_time'''.split()


class UsageV4(ctypes.Structure):
    _fields_ = [('uuid', ctypes.c_uint8 * 16)] + [
        (name, ctypes.c_uint64) for name in FIELDS]


class Timebase(ctypes.Structure):
    _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]


def decode(usage, numer, denom):
    if numer <= 0 or denom <= 0:
        raise ValueError('positive Mach timebase required')
    seconds = numer / denom / 1_000_000_000
    return dict(pidStartMachTicks=usage.proc_start_abstime,
                imageUuid=bytes(usage.uuid).hex(),
                userSeconds=usage.user_time * seconds,
                systemSeconds=usage.system_time * seconds,
                runnableSeconds=usage.runnable_time * seconds,
                reapedChildUserSeconds=usage.child_user_time * seconds,
                reapedChildSystemSeconds=usage.child_system_time * seconds,
                instructions=usage.instructions, cycles=usage.cycles,
                pageins=usage.pageins, footprintBytes=usage.phys_footprint)


class DarwinUsage:
    scope = 'owned-root-and-reaped-children-not-live-descendants'

    def __init__(self):
        if sys.platform != 'darwin':
            raise ValueError('Darwin process counters required')
        self.proc = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        self.proc.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        self.proc.proc_pid_rusage.restype = ctypes.c_int
        system = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        system.mach_timebase_info.argtypes = [ctypes.POINTER(Timebase)]
        system.mach_timebase_info.restype = ctypes.c_int
        self.timebase = Timebase()
        if system.mach_timebase_info(ctypes.byref(self.timebase)):
            raise ValueError('Mach timebase unavailable')
        decode(UsageV4(), self.timebase.numer, self.timebase.denom)

    def __call__(self, pid):
        usage = UsageV4()
        if self.proc.proc_pid_rusage(pid, 4, ctypes.byref(usage)):
            error = ctypes.get_errno()
            raise OSError(error, 'proc_pid_rusage unavailable for owned process')
        return decode(usage, self.timebase.numer, self.timebase.denom)


class DarwinGroupUsage(DarwinUsage):
    scope = 'sampled-owned-process-group-not-complete-descendant-lifetimes'

    def __init__(self):
        super().__init__()
        self.proc.proc_listpgrppids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        self.proc.proc_listpgrppids.restype = ctypes.c_int
        self.proc.proc_name.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.proc.proc_name.restype = ctypes.c_int

    def __call__(self, pid):
        if os.getpgid(pid) != pid:
            raise ValueError('isolated owned process-group leader required')
        members = (ctypes.c_int * 256)()
        count = self.proc.proc_listpgrppids(pid, members, ctypes.sizeof(members))
        if not 0 < count < len(members):
            raise ValueError('nonempty untruncated process-group inventory required')
        identifiers = set(members[:count])
        if pid not in identifiers or any(member <= 0 for member in identifiers):
            raise ValueError('positive group members including owned root required')
        rows, errors = [], []
        for member in sorted(identifiers):
            try:
                if os.getpgid(member) != pid:
                    raise ValueError('process left observed group')
                row = super().__call__(member)
                name = ctypes.create_string_buffer(256)
                length = self.proc.proc_name(member, name, len(name))
                if not 0 < length < len(name):
                    raise ValueError('current process name unavailable')
                row.update(pid=member, name=name.value.decode('utf-8', errors='replace'))
                rows.append(row)
            except (OSError, ValueError) as error:
                errors.append(dict(pid=member, error=str(error)))
        return dict(processes=rows, memberErrors=errors, observedMembers=len(identifiers),
                    completeDescendantCoverage=False)


def main():
    import argparse
    import json
    from pathlib import Path
    from bazel_host_environment import build_environment
    from native_object_manifest import digest
    from progressive_performance_gate import Limits
    from .context import data_path, retained_47, hardware_workers, Toolchain
    from .process import execute, spawn_events

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--home', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=('clean', 'build'), required=True)
    parser.add_argument('--observer', type=Path)
    parser.add_argument('--entry-probe', type=Path,
                        help='diagnostic preload before the unchanged build.ss, not root CLI timing')
    parser.add_argument('--reader-budget', type=Path,
                        help='completed import TSV to read without expansion; component diagnostic only')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    project = data_path(root, args.project)
    if not project.is_dir() or not (project / 'build.ss').is_file():
        parser.error('existing isolated project with build.ss required')
    output = data_path(root, args.output, fresh=True)
    toolchain = retained_47(root)
    if args.home:
        toolchain = Toolchain(toolchain.binary, data_path(root, args.home),
                              toolchain.expected_sha256).validate(root)
    driver = root / '.data/d1510-shell-substitution/bin'
    if digest(driver / 'gsc') != digest(toolchain.home / 'bin/gsc'):
        raise ValueError('selected GSC identity mismatch')
    workers = hardware_workers()
    env = toolchain.environment(build_environment(), package_home=project / '.gerbil',
                               load_paths=[project / '.gerbil/lib', toolchain.home / 'lib'],
                               workers=workers)
    env.update(PATH=str(toolchain.binary.parent) + ':' + env['PATH'],
               GERBIL_GSC=str(driver / 'gsc'), GERBIL_GCC=env['CC'],
               GERBIL_BUILD_VERBOSE='2', GAMBIT_EMBEDDED_NATIVE='0',
               GAMBOPT=f'~~bin={driver},~~lib={toolchain.home / "lib"},'
                       f'~~include={toolchain.home / "include"}')
    if args.phase == 'build' and any(
            path.is_file() and path.suffix[2:].isdigit()
            for path in (project / '.gerbil/lib').rglob('*.o[0-9]*')):
        raise ValueError('clean native project before build-prefix observation')
    observer = data_path(root, args.observer) if args.observer else None
    if observer is not None and not observer.is_file():
        parser.error('existing isolated diagnostic observer required')
    probe = args.entry_probe.resolve() if args.entry_probe else None
    if args.reader_budget and (probe or observer or args.phase != 'build'):
        parser.error('reader budget requires build phase without entry probe or observer')
    if probe is not None and (not probe.is_relative_to(root) or not probe.is_file()
                              or args.phase != 'build'):
        parser.error('existing project-local build-prefix probe required')
    output.mkdir()
    if observer is not None:
        traces = output / 'process-traces'
        traces.mkdir()
        env.update(DYLD_INSERT_LIBRARIES=str(observer), D1463_TRACE_DIR=str(traces))
    command = [str(toolchain.binary), args.phase]
    reader_input = data_path(root, args.reader_budget) if args.reader_budget else None
    read_paths = []
    source_hashes = {}
    if reader_input is not None:
        import csv
        with reader_input.open(newline='') as stream:
            for fields in csv.reader(stream, delimiter='\t', quoting=csv.QUOTE_NONE):
                if len(fields) != 8 or fields[0] != 'IMPORT-PREFIX':
                    raise ValueError('complete import TSV rows required')
                if fields[1] == '0' and fields[4] == '#t':
                    # Scheme write and JSON quote these ordinary filesystem strings identically.
                    path = Path(json.loads(fields[2])).resolve()
                    if not path.is_relative_to(root / '.data') or not path.is_file():
                        raise ValueError('existing isolated module source required')
                    if path not in read_paths:
                        read_paths.append(path)
        if not read_paths:
            raise ValueError('nonempty completed root module set required')
        source_hashes = {path: digest(path) for path in read_paths}
        command = [str(toolchain.binary.parent / 'gxi'),
                   str(Path(__file__).resolve().parents[1] / 'read_module_budget.scm'),
                   *map(str, read_paths)]
    if probe is not None:
        command = [str(toolchain.binary.parent / 'gxi'), '-L', str(probe),
                   str(project / 'build.ss'), 'compile']
        if (toolchain.binary.parent / 'gxi').resolve() != toolchain.binary:
            raise ValueError('selected gxi must resolve to frozen binary')
        env['GERBIL_DIAGNOSTIC_IMPORT_LOG'] = str(output / 'imports.tsv')
    row = execute(command, project, env, output / 'phase.log',
                  Limits(args.phase, complete=5 if reader_input else 50 if args.phase == 'build' else 30,
                         first=5 if args.phase == 'build' and not reader_input else None),
                  compile_only=args.phase == 'build' and not reader_input,
                  resource_reader=DarwinGroupUsage())
    row.update(scope='startup-resource-diagnostic-not-three-gate-admission',
               binarySha256=digest(toolchain.binary), physicalWorkers=workers,
               sourceBuildScriptSha256=digest(project / 'build.ss'))
    if probe is not None:
        row.update(entryScope='direct-unchanged-build-script-not-root-build-command',
                   entryProbeSha256=digest(probe))
    if reader_input is not None:
        row.update(scope='module-reader-component-not-three-gate-admission',
                   readerInputSha256=digest(reader_input), sourceCount=len(read_paths),
                   readerProbeSha256=digest(Path(command[1])))
        try:
            row['readerBudget'] = reader_result(output / 'phase.log', read_paths)
            row['sourceUnchanged'] = all(digest(path) == value
                                         for path, value in source_hashes.items())
            row['passed'] = row['passed'] and row['sourceUnchanged']
        except (ValueError, OSError) as error:
            row.update(passed=False, readerValidationFailure=str(error))
    if observer is not None:
        row['observerSha256'] = digest(observer)
        if row['resourceSamples']:
            try:
                row['processCensus'] = spawn_events(traces, row['resourceSamples'][0]['pid'])
            except ValueError as error:
                row['processCensusFailure'] = str(error)
    (output / 'report.json').write_text(json.dumps(row, indent=2) + '\n')
    summary = {key: value for key, value in row.items()
               if key not in ('resourceSamples', 'command')}
    summary.update(commandExecutable=Path(command[0]).name,
                   commandArgumentCount=len(command) - 1)
    print(json.dumps(summary))
    return 0 if row['passed'] else 1
