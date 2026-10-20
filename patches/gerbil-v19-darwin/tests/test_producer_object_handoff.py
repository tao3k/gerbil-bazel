from pathlib import Path
import shutil
import subprocess
import sys

import pytest


STACK = Path(__file__).resolve().parent.parent
ROOT = STACK.parents[1]


@pytest.mark.parametrize('flag, message', [
    ('--closed-link-producer-proof', 'producer proof requires the explicit single-pass closed-link candidate'),
    ('--closed-link-recipe-proof', 'recipe proof requires the explicit producer-proof candidate'),
    ('--native-object-capture', 'native capture requires an explicit bound single-pass closed-link candidate'),
    ('--native-object-check', 'native check requires the explicit native-capture candidate'),
    ('--fresh-produced-objects', 'fresh objects require a closed-link profile and exclude eager producer proof'),
])
@pytest.mark.parametrize('script, required', [
    ('run_d1510_progressive.py', ['--binary', 'absent', '--output', 'absent', '--test-home', 'absent']),
    ('run_complete_mcp_wave.py', ['--binary', 'absent', '--home', 'absent',
                                 '--project', 'absent', '--output', 'absent', '--cold-report', 'absent']),
])
def test_producer_proof_requires_single_pass_before_work(script, required, flag, message):
    result = subprocess.run(
        [sys.executable, str(STACK / 'tests' / script), *required, flag],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2
    assert message in result.stderr


@pytest.mark.parametrize('candidate_dir, patch_name, base_dir, files', [
    ('d1510-gerbil-closed-link-driver-v3', '0034-gerbil-darwin-producer-object-proof.patch',
     'd1510-gerbil-closed-link-driver-v2', ['driver.ss']),
    ('d1510-gerbil-fresh-produced-driver-v1', '0037-gerbil-darwin-fresh-produced-object-handoff.patch',
     'd1510-gerbil-closed-link-driver-v2', ['driver.ss']),
    ('d1510-gerbil-producer-recipe-driver-v1', '0039-gerbil-darwin-producer-recipe-guard.patch',
     'd1510-gerbil-closed-link-driver-v3', ['base.ss', 'driver.ss']),
])
def test_producer_patch_replays_exact_compiled_source(tmp_path, candidate_dir, patch_name,
                                                   base_dir, files):
    base = ROOT / '.data' / base_dir / 'source/compiler'
    candidate = ROOT / '.data' / candidate_dir / 'source/compiler'
    if any(not (directory / name).is_file()
           for directory in (base, candidate) for name in files):
        pytest.skip('isolated compiler source fixtures unavailable')
    source = tmp_path / 'src/gerbil/compiler'
    source.mkdir(parents=True)
    for name in files:
        shutil.copyfile(base / name, source / name)
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    patch = STACK / patch_name
    for command in (['git', 'apply', '--check', str(patch)], ['git', 'apply', str(patch)]):
        subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    for name in files:
        assert (source / name).read_bytes() == (candidate / name).read_bytes()
    subprocess.run(['git', 'apply', '--reverse', str(patch)], cwd=tmp_path, check=True)
    for name in files:
        assert (source / name).read_bytes() == (base / name).read_bytes()


def test_producer_switch_is_recorded_forwarded_and_checked():
    cold = (STACK / 'tests/run_d1510_progressive.py').read_text()
    complete = (STACK / 'tests/run_complete_mcp_wave.py').read_text()
    assert "env.pop('GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF', None)" in cold
    assert 'closedLinkProducerProofEnabled={args.closed_link_producer_proof!r}' in cold
    assert "*(['--closed-link-producer-proof'] if args.closed_link_producer_proof else [])" in cold
    assert "args.closed_link_producer_proof != cold.get('closedLinkProducerProofEnabled', False)" in complete
    assert "base['GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF'] = '1'" in complete
