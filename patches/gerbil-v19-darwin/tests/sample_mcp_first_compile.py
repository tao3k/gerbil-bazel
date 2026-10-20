#!/usr/bin/env python3
"""Sample only the real MCP first-compile window; deliberately abort thereafter."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
from threading import Thread
import time

from bazel_host_environment import build_environment
from macho_image_dependencies import validate_packed_image_inventory
from build_runtime_image_composition import SCOPE as COMPOSITION_SCOPE, validate_composed_runtime


def first_window_sampler(pid, output, hardware):
    if hardware:
        return ['xcrun', 'xctrace', 'record', '--template', 'CPU Profiler',
                '--attach', str(pid), '--output', str(output/'profile.trace'),
                '--time-limit', '5s', '--no-prompt']
    return ['/usr/bin/sample', str(pid), '2', '1', '-file',
            str(output/'first-window.sample.txt')]


def first_window_observer(pid, output, hardware, verify_only):
    if verify_only:
        if hardware:
            raise ValueError('child verification cannot attach a hardware recorder')
        return None
    return first_window_sampler(pid, output, hardware)


def observed_child_usage(before, after):
    return dict(userCpuSeconds=after.ru_utime-before.ru_utime,
                systemCpuSeconds=after.ru_stime-before.ru_stime,
                voluntaryContextSwitches=after.ru_nvcsw-before.ru_nvcsw,
                involuntaryContextSwitches=after.ru_nivcsw-before.ru_nivcsw,
                scope='reaped-supervisor-children-including-observers-not-active-cycle-attribution')


def first_window_target(parent_pid, rows):
    for row in rows:
        if (len(row) == 2 and 'build.ss' in row[1] and 'compile' in row[1]
                and Path(row[1].split()[0]).name in ('gxi', 'gerbil')):
            return int(row[0]), 'build-child'
    return parent_pid, 'official-parent'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary-source", type=Path)
    parser.add_argument("--native-binary", type=Path)
    parser.add_argument("--embedded-native", action="store_true")
    parser.add_argument("--require-build-child", action="store_true")
    parser.add_argument("--image-receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--head")
    parser.add_argument("--observe-first-only", action="store_true")
    parser.add_argument("--clean-only", action="store_true")
    parser.add_argument("--sample-clean-only", action="store_true")
    parser.add_argument("--sample-first-window", action="store_true")
    parser.add_argument("--verify-child-only", action="store_true")
    parser.add_argument("--hardware-first-window", action="store_true")
    parser.add_argument("--path-cost", action="store_true")
    args = parser.parse_args()
    if args.sample_clean_only and not args.clean_only:
        parser.error('clean sampling requires clean-only mode')
    if args.hardware_first_window and not args.sample_first_window:
        parser.error('hardware recording requires real first-window sampling')
    if args.verify_child_only and (not args.require_build_child or args.sample_first_window
                                  or args.hardware_first_window or args.observe_first_only or args.clean_only):
        parser.error('verification-only requires a real builder child and strict unsampled build mode')
    if args.clean_only and any((args.observe_first_only, args.sample_first_window, args.hardware_first_window, args.path_cost)):
        parser.error('clean-only cannot qualify first-window sampling or path costs')
    repo = Path(__file__).resolve().parents[3]
    project, home, output = args.project.resolve(), args.source.resolve() / "build", args.output.resolve()
    binary_home = args.binary_source.resolve() / "build" if args.binary_source else home
    binary = args.native_binary.resolve() if args.native_binary else binary_home / 'bin/gerbil'
    if args.native_binary:
        if args.binary_source or args.image_receipt or not binary.is_relative_to(repo / '.data'):
            parser.error('flat native binary requires isolated data and no alternate image home')
        native = json.loads((binary.parent / 'report.json').read_text())
        if (not native.get('qualified') or hashlib.sha256(binary.read_bytes()).hexdigest() != native.get('binarySha256')
                or (binary.parent / 'gxi').resolve() != binary):
            parser.error('flat native binary receipt, digest or shebang child differs')
    if args.embedded_native and not args.native_binary:
        parser.error('embedded lookup observation requires an explicit qualified native binary')
    if args.require_build_child and not (args.sample_first_window or args.verify_child_only):
        parser.error('required builder child needs first-window sampling or verification')
    if args.path_cost and not (binary_home.parent / 'path-cost-probe-preparation.json').is_file():
        parser.error('path cost observation requires its isolated counter source')
    path_preparation = None
    if args.path_cost:
        path_preparation = json.loads((binary_home.parent / 'path-cost-probe-preparation.json').read_text())
        native_source = binary_home.parent / 'src/gambit/lib'
        if hashlib.sha256((native_source / 'gambit-path-cost-probe.h').read_bytes()).hexdigest() != path_preparation['headerSha256']:
            parser.error('native path cost header differs from preparation receipt')
        for filename, hashes in path_preparation['sourceHashes'].items():
            if hashlib.sha256((native_source / filename).read_bytes()).hexdigest() != hashes['diagnostic']:
                parser.error('native path cost source differs from preparation receipt')
    if platform.system() != "Darwin" or not all(p.is_relative_to(repo / ".data") for p in (project, home, binary_home, output)):
        parser.error("Darwin diagnostic under project .data required")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.pop('GAMBIT_DARWIN_PATH_COST_PREFIX', None)
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    for key in ("GERBIL_BUILD_PREFIX", "GAMBIT_HOST_GROUP_BUDGET", "GAMBIT_DARWIN_COST_TRACE"):
        env.pop(key, None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / ".gerbil"),
               GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{home / 'lib'}", GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{binary.parent}:{home / 'bin'}:{env['PATH']}", GERBIL_BUILD_CORES=str(cores),
               GERBIL_BUILD_VERBOSE="2", GERBIL_GCC=env["GERBIL_GNU_GCC"])
    env['GAMBIT_EMBEDDED_NATIVE'] = '1' if args.embedded_native else '0'
    report = {"performanceQualified": False, "qualified": False, "diagnosticOnly": True,
              "buildCompleted": False, "projectHead": subprocess.check_output(
                  ["git", "-C", str(project), "rev-parse", "HEAD"], text=True).strip(), "cores": cores}
    report.update(partialRuntimeProfile=bool(args.binary_source or args.native_binary),
                  runtimeHome=str(home.relative_to(repo)), binaryHome=str(binary_home.relative_to(repo)))
    report['nativeBinaryRef'] = binary.relative_to(repo).as_posix()
    if args.image_receipt:
        image_receipt = args.image_receipt.resolve()
        if not image_receipt.is_relative_to(repo / '.data') or args.binary_source:
            parser.error('isolated image receipt requires whole candidate home')
        image_build = json.loads(image_receipt.read_text())
        composed = image_build.get('scope') == COMPOSITION_SCOPE
        if (image_build.get('qualified') is not True or image_build.get('officialToolsIncluded') is not True
                or image_build.get('originalGambitMacroInputsUsed') is not True
                or not composed and image_build.get('binaryHashesUnchanged') is not True
                or image_build.get('scope') not in ('current-staging-native-preload-image-packing-prototype', COMPOSITION_SCOPE)
                or (repo / image_build['candidate']).resolve() / 'build' != home
                or hashlib.sha256((home / 'bin/gsc').read_bytes()).hexdigest() != image_build['gscSha256']):
            parser.error('completed current-input official-tool image build required')
        validate_packed_image_inventory(home, image_build)
        if composed:
            original_home = (repo/image_build['originalHome']).resolve()
            if not original_home.is_relative_to(repo/'.data'):
                parser.error('isolated original composition runtime required')
            validate_composed_runtime(home, image_build, original_home)
        report.update(imageBuildReceiptSha256=hashlib.sha256(image_receipt.read_bytes()).hexdigest(),
                      packedImageHashesLocked=True, composedRuntime=composed)
    if args.head and report["projectHead"] != args.head:
        parser.error("project head differs from the requested identity")
    report.update(observeFirstOnly=args.observe_first_only, strictOutputGapSeconds=10,
                  strictOutputGateFailed=False, hostLoadStart=os.getloadavg(),
                  hardwareFirstWindow=args.hardware_first_window,
                  binarySha256={'gerbil': hashlib.sha256(binary.read_bytes()).hexdigest(),
                                'gxi': hashlib.sha256((binary.parent / 'gxi').read_bytes()).hexdigest(),
                                'gsc': hashlib.sha256((home / 'bin/gsc').read_bytes()).hexdigest()},
                  preparedSourceSha256={name: hashlib.sha256((project / name).read_bytes()).hexdigest()
                                       for name in ("build.ss", "util/compat.ss", "util/regex.ss", "data/embedded.ss")})
    report['pathCostObservation'] = args.path_cost
    report['embeddedNativeEnabled'] = args.embedded_native
    report['verifyChildOnly'] = args.verify_child_only
    if path_preparation:
        report['pathCostPreparation'] = path_preparation
    sampler = None
    clean_sample_log = None
    process = None
    next_process_query = 0
    target_observed = False
    def interrupted(signum, frame):
        raise InterruptedError('first-window observer interrupted; reap owned product groups')
    signal.signal(signal.SIGTERM, interrupted)
    usage_started = resource.getrusage(resource.RUSAGE_CHILDREN)
    observation_started = time.monotonic()
    try:
        if args.path_cost:
            env['GAMBIT_DARWIN_PATH_COST_PREFIX'] = str(output / 'clean-path-cost')
        with (output / "clean.log").open("w") as log:
            clean_started = time.monotonic()
            process = subprocess.Popen([str(binary), "clean"], cwd=project, env=env,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            if args.sample_clean_only:
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    children = subprocess.run(['pgrep', '-P', str(process.pid), '-fl'],
                                              capture_output=True, text=True, timeout=1)
                    build_children = [line.split(None, 1) for line in children.stdout.splitlines()
                                      if 'build.ss' in line]
                    pid = int(build_children[0][0]) if build_children else process.pid
                    report.update(cleanSampledPid=pid, cleanSampleTarget=('build-child' if build_children else 'official-parent'))
                    clean_sample_log = (output/'clean-sampler.log').open('w')
                    sampler = subprocess.Popen(['/usr/bin/sample', str(pid), '2', '1', '-file',
                                                str(output / 'clean.sample.txt')],
                                               stdout=clean_sample_log, stderr=subprocess.STDOUT, start_new_session=True)
                    print(f'CLEAN-SAMPLE-START target={report["cleanSampleTarget"]}', flush=True)
            status = process.wait(timeout=max(0.001, 30-(time.monotonic()-clean_started)))
            report['cleanWallSeconds'] = time.monotonic()-clean_started
            if sampler is not None:
                report['cleanSampleExitCode'] = sampler.wait(timeout=5)
            if status:
                raise subprocess.CalledProcessError(status, process.args)
        if "*** ERROR" in (output / "clean.log").read_text():
            raise RuntimeError("official clean reported an error")
        remaining = len(list((project / ".gerbil/lib/gerbil-mcp").rglob("*.o1")))
        report.update(officialCleanPassed=True, nativeImagesAfterClean=remaining)
        if remaining:
            raise RuntimeError("official clean left project native images")
        if args.clean_only:
            report.update(qualified=True, scope='official-clean-only-correctness-not-first-log',
                          cleanOnly=True)
            print('OFFICIAL-CLEAN-OK', flush=True)
            return
        started = time.monotonic()
        if args.path_cost:
            env['GAMBIT_DARWIN_PATH_COST_PREFIX'] = str(output / 'build-path-cost')
        last_output = [started]
        events = {}
        with (output / "build.log").open("w") as log, (output / "sampler.log").open("w") as sample_log:
            process = subprocess.Popen([str(binary), "build"], cwd=project, env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)

            def collect():
                for line in process.stdout:
                    now = time.monotonic()
                    gap = now - last_output[0]
                    events["maximumOutputGapSeconds"] = max(events.get("maximumOutputGapSeconds", 0), gap)
                    if gap > 10:
                        report["strictOutputGateFailed"] = True
                    last_output[0] = now
                    log.write(line)
                    log.flush()
                    if line.startswith("... compile "):
                        events.setdefault("firstCompileSeconds", now - started)

            reader = Thread(target=collect, daemon=True)
            reader.start()
            while process.poll() is None and "firstCompileSeconds" not in events:
                time.sleep(0.25)
                now = time.monotonic()
                if now - last_output[0] > 10:
                    report["strictOutputGateFailed"] = True
                if (now - last_output[0] > 10 and not args.observe_first_only) or now - started > (60 if args.observe_first_only else 30):
                    raise TimeoutError("startup diagnostic exceeded strict output/budget gate")
                if args.observe_first_only and not args.sample_first_window:
                    continue
                if target_observed or now < next_process_query:
                    continue
                next_process_query = now + 1
                try:
                    children = subprocess.run(
                        ["pgrep", "-P", str(process.pid), "-fl"], text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
                    rows = [line.split(None, 1) for line in children.stdout.splitlines()]
                except subprocess.TimeoutExpired:
                    report["processObservationTimeouts"] = report.get("processObservationTimeouts", 0) + 1
                    continue
                if now - started >= (0.25 if args.hardware_first_window or args.verify_child_only else 3):
                    pid, target = first_window_target(process.pid, rows)
                    if args.require_build_child:
                        if target != 'build-child':
                            continue
                        libproc = ctypes.CDLL('/usr/lib/libproc.dylib')
                        libproc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
                        libproc.proc_pidpath.restype = ctypes.c_int
                        path_buffer = ctypes.create_string_buffer(4096)
                        if libproc.proc_pidpath(pid, path_buffer, len(path_buffer)) <= 0:
                            raise RuntimeError('actual builder child executable cannot be resolved')
                        observed = Path(os.fsdecode(path_buffer.value)).resolve()
                        if observed != binary.resolve() or hashlib.sha256(observed.read_bytes()).hexdigest() != report['binarySha256']['gerbil']:
                            raise RuntimeError('actual builder child binary differs')
                        report['sampledChildBinarySha256'] = report['binarySha256']['gerbil']
                        report['actualBuilderChildVerified'] = True
                    report["observedPid"] = pid
                    report["sampleTarget"] = target
                    report["sampleStartSeconds"] = now - started
                    command = first_window_observer(pid, output, args.hardware_first_window, args.verify_child_only)
                    if command is not None:
                        report["sampledPid"] = pid
                        sampler = subprocess.Popen(command, stdout=sample_log,
                                                   stderr=subprocess.STDOUT, start_new_session=True)
                    target_observed = True
                    report['samplerAttached'] = sampler is not None
                    action = 'CHILD-VERIFIED' if args.verify_child_only else 'SAMPLE-START'
                    print(f"{action} {target} pid={pid} at {now - started:.3f}s", flush=True)
            report.update(events)
            if "firstCompileSeconds" not in events:
                raise RuntimeError("process exited before a real compile line")
            print(f"FIRST-COMPILE {events['firstCompileSeconds']:.3f}s; diagnostic stops here", flush=True)
            if process.poll() is not None:
                report["monitoringOverranFirstCompile"] = True
                raise RuntimeError("monitoring overran first compilation; not a first-window receipt")
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
            reader.join(timeout=5)
            if args.verify_child_only and not report.get('actualBuilderChildVerified'):
                raise RuntimeError('actual build-script child was not verified')
            if sampler is None and not args.verify_child_only and (not args.observe_first_only or args.sample_first_window):
                raise RuntimeError("build-script process was not sampled")
            report["buildDeliberatelyStoppedAfterFirstCompile"] = True
            report["buildExitCode"] = process.returncode
            if sampler is not None:
                report["sampleExitCode"] = sampler.wait(timeout=40 if args.hardware_first_window else 15)
                report["sampleCompleted"] = sampler.returncode == 0 and (
                    (output/'profile.trace').is_dir() if args.hardware_first_window
                    else (output/'first-window.sample.txt').is_file())
                if args.hardware_first_window:
                    if not report['sampleCompleted']:
                        raise RuntimeError('actual first-window hardware recording failed')
                    toc = subprocess.check_output(['xcrun', 'xctrace', 'export', '--input',
                        str(output/'profile.trace'), '--toc'], env=env, timeout=120)
                    (output/'toc.xml').write_bytes(toc)
                    subprocess.run(['xcrun', 'xctrace', 'export', '--input', str(output/'profile.trace'),
                        '--xpath', '/trace-toc/run[@number="1"]/data/table[@schema="cpu-profile"]',
                        '--output', str(output/'cpu-profile.xml')], env=env, check=True, timeout=120,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    report['hardwareRecordingExported'] = True
        if args.path_cost:
            snapshots = []
            for path in sorted(output.glob('*-path-cost.*.json')):
                snapshots.append({'file': path.name, **json.loads(path.read_text())})
            if not snapshots or any(row['measurementFailures'] for row in snapshots):
                raise RuntimeError('native path costs require actual valid snapshots')
            if not any(row['costs'][1]['calls'] for row in snapshots if row['file'].startswith('build-')):
                raise RuntimeError('native path costs did not cover real build normalization')
            report['pathCostSnapshots'] = snapshots
            report['pathCostScope'] = 'partial-native-cost-observation-no-performance-nested-costs-not-additive'
    except BaseException as error:
        report["failure"] = repr(error)
        raise
    finally:
        for child in (process, sampler):
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
        report["hostLoadEnd"] = os.getloadavg()
        report['observedChildUsage'] = observed_child_usage(
            usage_started, resource.getrusage(resource.RUSAGE_CHILDREN))
        report['observationWallSeconds'] = time.monotonic()-observation_started
        if clean_sample_log is not None:
            clean_sample_log.close()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
