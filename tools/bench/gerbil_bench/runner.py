import concurrent.futures
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time

from .execution import Budget, execute
from .storage import atomic_json, digest, files, lease, relative


def workers():
    if platform.system() == 'Darwin':
        return int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    return len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count() or 1


def load_profile(path):
    profile = json.loads(path.read_text())
    if profile.get('schema') != 1 or not re.fullmatch(r'[a-zA-Z0-9_-]+', profile['name']):
        raise ValueError('schema 1 and safe package name required')
    for phase in ('clean', 'build'):
        if not isinstance(profile[phase], list) or not profile[phase]:
            raise ValueError('argument-vector commands required')
        if profile[phase][:2] != ['{gerbil}', phase]:
            raise ValueError('only selected gerbil clean/build commands permitted')
    tests = profile['tests']
    if not tests or any(not isinstance(test, list) or not test for test in tests):
        raise ValueError('explicit complete test command inventory required')
    for test in tests:
        if test[:2] != ['{gerbil}', 'test']:
            raise ValueError('tests must invoke the selected gerbil test command')
    return profile


def validate_inventory(profile, source):
    declared = [args[-1] for args in profile['tests']]
    if len(set(declared)) != len(declared):
        raise ValueError('duplicate test inventory')
    for name in declared:
        path = relative(source, name)
        if not path.is_file() or path.suffix != '.ss':
            raise ValueError('each declared test file must exist')
    discovered = {str(path.relative_to(source)) for pattern in profile['testGlobs']
                  for path in source.glob(pattern) if path.is_file()}
    if not discovered or discovered != set(declared):
        raise ValueError('complete declared and discovered test inventories must match')
    return {name: digest(source / name) for name in declared}


def run(root, profile_path, toolchain_path, identifier, rounds=3):
    root = root.resolve()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', identifier) or rounds not in (1, 2, 3):
        raise ValueError('safe fresh run ID and 1-3 rounds required')
    profile = load_profile(profile_path)
    toolchain = json.loads(toolchain_path.read_text())
    source = relative(root, profile['source'])
    if not source.is_relative_to(root / '.data'):
        raise ValueError('package source must be isolated in .data')
    inventory = validate_inventory(profile, source)
    paths = {key: relative(root, toolchain[key]) for key in ('binary', 'home', 'driver')}
    paths['gcc'] = Path(os.environ[toolchain['gccEnvironment']]).resolve(strict=True)
    if any(not paths[key].is_relative_to(root / '.data') for key in ('binary', 'home', 'driver')):
        raise ValueError('isolated .data toolchain required')
    inputs = [paths['binary'], paths['driver'] / 'gsc', paths['driver'] / 'gambuild-C']
    inputs.extend(relative(root, name) for name in toolchain.get('additionalInputs', []))
    hashes = {str(path.relative_to(root)): digest(path) for path in inputs}
    gcc_hash = digest(paths['gcc'])
    if hashes[str(paths['binary'].relative_to(root))] != toolchain['binarySha256']:
        raise ValueError('runtime identity mismatch')
    version = subprocess.check_output([str(paths['gcc']), '--version'], text=True)
    if 'clang' in version.lower() or not ('gcc' in version.lower() or 'Free Software Foundation' in version):
        raise ValueError('explicit GNU GCC required')
    cores = workers()
    output = relative(root, '.data/bench/runs/' + identifier)
    if output != root / '.data/bench/runs' / identifier:
        raise ValueError('managed output ancestors may not be symlinks')
    with lease(root):
        output.mkdir(parents=True, exist_ok=False)
        source_hashes = {name: digest(source / name) for name, _, _ in files(source, exclude=('.git', '.gerbil'))}
        receipt = dict(schema=1, package=profile['name'], decision='DENY', state='running',
                       workers=cores, rounds=rounds, runs=[], inputHashes=hashes, gccSha256=gcc_hash,
                       sourceHashes=source_hashes, profileSha256=digest(profile_path),
                       testInventory=inventory,
                       toolchainSha256=digest(toolchain_path),
                       protectedPaths=[str(path.relative_to(root)) for path in
                                       [source, *paths.values(), *(item.resolve() for item in inputs)]
                                       if path.is_relative_to(root / '.data')],
                       gates=dict(firstLogSeconds=5, buildSeconds=50, testSeconds=112))
        atomic_json(output / 'receipt.json', receipt)
        try:
            for index in range(rounds):
                folder = output / str(index)
                folder.mkdir()
                project = folder / 'project'
                shutil.copytree(source, project, ignore=shutil.ignore_patterns('.git', '.gerbil'))
                row = dict(index=index, passed=False, fixtureHashes={})
                receipt['runs'].append(row)
                for fixture in profile.get('fixturePatches', []):
                    patch = relative(root, fixture)
                    if not patch.is_relative_to(root / 'tools') and not patch.is_relative_to(root / 'patches'):
                        raise ValueError('fixture patches must be Git-owned workspace inputs')
                    row['fixtureHashes'][fixture] = digest(patch)
                    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=project, check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(['git', 'apply', str(patch)], cwd=project, check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                copied_sources = {name: digest(project / name) for name in source_hashes}
                entry = folder / 'bin'
                entry.mkdir()
                for name in ('gerbil', 'gxi', 'gxc', 'gxpkg', 'gxtest'):
                    (entry / name).symlink_to(paths['binary'])
                for name in ('gsc', 'gsi', 'gambuild-C'):
                    target = paths['home'] / 'bin/gsi' if name == 'gsi' else paths['driver'] / name
                    (entry / name).symlink_to(target)
                env = {key: value for key, value in os.environ.items()
                       if not key.startswith(('GERBIL_', 'GAMBIT_')) and key != 'GAMBOPT'}
                env.update(PATH=f'{entry}:{env.get("PATH", "")}', CC=str(paths['gcc']), GERBIL_HOME=str(paths['home']),
                           GERBIL_PATH=str(project / '.gerbil'), GERBIL_BUILD_CORES=str(cores),
                           GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{paths["home"] / "lib"}:{project}',
                           GERBIL_GSC=str(entry / 'gsc'), GERBIL_GXC=str(entry / 'gxc'),
                           GERBIL_GCC=str(paths['gcc']), GERBIL_GNU_GCC=str(paths['gcc']),
                           GERBIL_BUILD_VERBOSE='2', GAMBIT_EMBEDDED_NATIVE='0',
                           GAMBOPT=f'~~bin={entry},~~lib={paths["home"] / "lib"},~~include={paths["home"] / "include"}')
                for key, value in profile.get('environment', {}).items():
                    if key in env or not re.fullmatch(r'[A-Z][A-Z0-9_]+', key):
                        raise ValueError('fixture environment cannot override selected toolchain')
                    env[key] = value.replace('{project}', str(project)).replace('{bin}', str(entry))
                tracked_environment = ('CC', 'CXX', 'CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'LDFLAGS',
                    'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'GERBIL_CC_OPTIONS', 'GERBIL_HOME',
                    'GERBIL_GSC', 'GERBIL_GXC', 'GERBIL_GCC', 'GERBIL_BUILD_CORES',
                    'GERBIL_BUILD_VERBOSE', 'GAMBOPT', 'GAMBIT_EMBEDDED_NATIVE')
                def redact(value):
                    return value.replace(str(root), '{workspace}').replace(str(paths['gcc']), '{gnu-gcc}').replace(
                        str(Path.home()), '{user-home}')
                row['environment'] = {key: redact(env[key]) for key in tracked_environment if key in env}
                def command(args):
                    if args[0] != '{gerbil}':
                        raise ValueError('commands must select {gerbil}, never a global runtime')
                    return [str(entry / 'gerbil'), *args[1:]]
                row['clean'] = execute(command(profile['clean']), project, env, folder / 'clean.log', Budget(30))
                if not row['clean']['passed']:
                    break
                build = Budget(50, 5)
                row['build'] = execute(command(profile['build']), project, env, folder / 'build.log',
                                       build, compile_only=True)
                row['firstCompileSeconds'] = build.first_elapsed
                if not row['build']['passed'] or build.first_elapsed is None:
                    break
                artifacts = {str(path.relative_to(project)): digest(path)
                             for pattern in profile['artifactGlobs'] for path in project.glob(pattern)
                             if path.is_file()}
                if not artifacts:
                    row['failure'] = 'build-produced-no-declared-artifacts'
                    break
                row['artifactHashes'] = artifacts
                test_budget = Budget(112, 5)
                started = time.monotonic()
                def test(item):
                    number, args = item
                    temporary = folder / f'test-{number}-tmp'
                    temporary.mkdir()
                    test_env = dict(env, TMPDIR=str(temporary))
                    result = execute(command(args), project, test_env, folder / f'test-{number}.log',
                                     test_budget, final_ok=True)
                    result['testFile'] = args[-1]
                    return result
                with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as pool:
                    row['tests'] = list(pool.map(test, enumerate(profile['tests'])))
                row['testSeconds'] = time.monotonic() - started
                row['firstTestLogSeconds'] = test_budget.first_elapsed
                row['copiedSourcesUnchanged'] = all((project / name).is_file() and
                    digest(project / name) == value for name, value in copied_sources.items())
                row['testArtifactsUnchanged'] = all((project / name).is_file() and
                    digest(project / name) == value for name, value in artifacts.items())
                row['passed'] = (all(item['passed'] for item in row['tests']) and
                                 not test_budget.denied and row['testSeconds'] <= 112 and
                                 row['copiedSourcesUnchanged'] and row['testArtifactsUnchanged'])
                if not row['passed']:
                    break
                atomic_json(output / 'receipt.json', receipt)
            unchanged = all(digest(root / name) == value for name, value in hashes.items()) and digest(paths['gcc']) == gcc_hash
            source_unchanged = source_hashes == {name: digest(source / name) for name, _, _ in
                                               files(source, exclude=('.git', '.gerbil'))}
            receipt.update(inputsUnchanged=unchanged, sourceUnchanged=source_unchanged)
            receipt['decision'] = 'ALLOW' if (unchanged and source_unchanged and
                len(receipt['runs']) == rounds and all(row['passed'] for row in receipt['runs'])) else 'DENY'
        except BaseException as error:
            receipt['failureType'] = type(error).__name__
            raise
        finally:
            receipt['state'] = 'terminal'
            atomic_json(output / 'receipt.json', receipt)
    return receipt
