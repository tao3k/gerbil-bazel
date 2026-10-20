"""Compare captured configuration and work without repeating a build."""
import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def normalize(value, project):
    if isinstance(value, str):
        return value.replace(str(project), '<project>').replace(str(ROOT), '<root>')
    if isinstance(value, dict):
        return {normalize(k, project): normalize(v, project) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, project) for v in value]
    return value


def work(directory):
    lines = (directory / 'build.log').read_text().splitlines()
    project = directory / 'project'
    return Counter(normalize(line, project) for line in lines
                   if line.startswith(('... compile ', '... execute compile job ')))


def compare(old, new):
    before = normalize(json.loads((old / 'configuration.json').read_text()), old / 'project')
    after = normalize(json.loads((new / 'configuration.json').read_text()), new / 'project')
    keys = ('environment', 'files', 'gccVersion', 'driverSha256')
    configuration = {key: before[key] == after[key] for key in keys}
    old_work, new_work = work(old), work(new)
    return dict(configurationMatches=configuration,
                compileWorkMatches=old_work == new_work,
                oldWorkCount=sum(old_work.values()), newWorkCount=sum(new_work.values()),
                addedWork=list((new_work - old_work).elements()),
                removedWork=list((old_work - new_work).elements()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    old = ROOT / '.data/d1510-source-loader-cold-abba'
    new = ROOT / '.data/d1510-source-loader-cold-repeat-exact-abba'
    before = json.loads((old / 'report.json').read_text())
    after = json.loads((new / 'report.json').read_text())
    result = dict(scope='captured-configuration-and-work-not-causal-timing-diagnosis',
                  reportIdentityMatches={key: before[key] == after[key] for key in
                                         ('projectHead', 'cores', 'sourceHashes', 'candidateDriverSha256')},
                  runs=[])
    for index, (a, b) in enumerate(zip(before['runs'], after['runs'], strict=True)):
        assert a['role'] == b['role']
        directory = f"{index}-{a['role']}"
        result['runs'].append(dict(role=a['role'],
            binaryMatches=a['binarySha256'] == b['binarySha256'],
            historicalSeconds=a['buildWallSeconds'], repeatSeconds=b['buildWallSeconds'],
            **compare(old / directory, new / directory)))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
