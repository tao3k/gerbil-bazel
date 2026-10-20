"""Join native first-failed-guard counts to generated source, never timing."""
import argparse
import json
from pathlib import Path


def rows(text, width):
    result = []
    for line in text.splitlines():
        row = tuple(map(int, line.split()))
        if len(row) != width or min(row) < 0:
            raise ValueError('invalid native counter row')
        result.append(row)
    return result


def summarize(profile, attempts, failures):
    sites = profile['guardedReadOnlyTraces']
    reached, guard_counts = {}, {}
    for site, count, hits, cached in rows(attempts, 4):
        if site >= len(sites) or site in reached or hits > count or cached:
            raise ValueError('invalid or duplicate allocation site')
        reached[site] = (count, hits)
    for site, guard, count in rows(failures, 3):
        if (site not in reached or guard >= len(sites[site]['allocationGuardMisses'])
                or (site, guard) in guard_counts):
            raise ValueError('invalid or duplicate allocation guard')
        guard_counts[site, guard] = count
    details = []
    for site, (count, hits) in reached.items():
        guards = [{'guard': guard, 'count': value,
                   'condition': sites[site]['allocationGuardMisses'][guard]}
                  for (owner, guard), value in guard_counts.items() if owner == site]
        missed = sum(row['count'] for row in guards)
        if missed + hits > count:
            raise ValueError('multiple first failures counted for one attempt')
        details.append(dict(site=site, module=sites[site]['module'], line=sites[site]['line'],
                            attempts=count, successes=hits, otherMisses=count-hits-missed,
                            callsRemoved=sites[site]['callsRemoved'],
                            guards=sorted(guards, key=lambda row: -row['count'])))
    return dict(scope='native-allocation-coverage-not-performance', performanceQualified=False,
                attempts=sum(row['attempts'] for row in details),
                successes=sum(row['successes'] for row in details),
                sites=sorted(details, key=lambda row: -row['attempts']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[3] / '.data'
    if not all(path.resolve().is_relative_to(data) for path in (args.profile, args.run, args.output)):
        parser.error('all evidence must remain in project .data')
    profile = json.loads((args.profile / 'report.json').read_text())
    run = json.loads((args.run / 'report.json').read_text())
    if not (profile['qualified'] and profile['diagnosticOnly'] and run['qualified']
            and profile['binaryHashes']['gxi'] == run['binaryHashes']['candidate']
            and len(run['runs']) == 1 and run['runs'][0]['exitCode'] == 0
            and run['runs'][0]['preparedModules'] == 187):
        raise ValueError('requires the exact qualified diagnostic binary and complete MCP preparation')
    result = summarize(profile, (args.run / 'counts.txt').read_text(),
                       (args.run / 'counts.txt.guards').read_text())
    result['binarySha256'] = profile['binaryHashes']['gxi']
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({key: result[key] for key in ('attempts', 'successes')}))


if __name__ == '__main__':
    main()
