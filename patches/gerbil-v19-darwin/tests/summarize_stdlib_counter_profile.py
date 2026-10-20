"""Summarize named CPU metric contributions, not removable wall-time fractions."""
import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from native_object_manifest import digest
from experiment_framework.xml_evidence import XmlTable
from experiment_framework.context import data_path


CATEGORIES = ('processing', 'discarded', 'delivery', 'useful')
COLUMNS = ['timestamp', 'duration', 'process', 'metric-value-int',
           'metric-value-double', 'metric-name', 'is-precise']


def precise_metric_groups(tree, pid):
    table = XmlTable(tree, COLUMNS)
    resolve = table.resolve
    groups = {}
    skipped = 0
    for fields in table.rows():
        process_pid = fields[2].find('pid')
        if process_pid is None or int(resolve(process_pid).text) != pid:
            raise ValueError('different process cannot contribute metrics')
        precise = fields[6].text
        if precise not in ('0', '1'):
            raise ValueError('invalid precision flag')
        if precise == '0':
            skipped += 1
            continue
        start, duration = int(fields[0].text), int(fields[1].text)
        if start < 0 or duration <= 0:
            raise ValueError('invalid interval')
        name = fields[5].text
        value = int(fields[3].text) if name == 'cycle' else float(fields[4].text)
        if name not in (*CATEGORIES, 'cycle') or not math.isfinite(value) or value < 0:
            raise ValueError('invalid named metric')
        group = groups.setdefault((start, duration), {})
        if name in group:
            raise ValueError('duplicate interval metric')
        group[name] = value
    if not groups:
        raise ValueError('no precise target metric buckets')
    return groups, skipped


def summarize(tree, pid):
    groups, skipped = precise_metric_groups(tree, pid)
    previous_end = 0
    weighted = {name: [] for name in CATEGORIES}
    cycles = []
    for (start, duration), group in sorted(groups.items()):
        if start < previous_end or set(group) != {*CATEGORIES, 'cycle'}:
            raise ValueError('overlapping or incomplete target bucket')
        previous_end = start + duration
        mass = math.fsum(group[name] for name in CATEGORIES)
        if group['cycle'] > 0 and mass <= 0:
            raise ValueError('positive cycles without metric contributions')
        cycles.append(group['cycle'])
        if mass > 0:
            for name in CATEGORIES:
                weighted[name].append(group[name] / mass * group['cycle'])
    total = sum(cycles)
    if total <= 0:
        raise ValueError('no positive hardware cycles')
    shares = {name: math.fsum(values) / total for name, values in weighted.items()}
    if not math.isclose(math.fsum(shares.values()), 1, abs_tol=1e-9):
        raise ValueError('metric share normalization failed')
    return dict(preciseBuckets=len(groups), coarseRowsExcluded=skipped,
                recordedCycles=total, cycleWeightedNormalizedMetricShares=shares,
                firstBucketNanoseconds=min(start for start, _ in groups),
                lastBucketEndNanoseconds=previous_end,
                interpretation='normalized named metric mass, not removable runtime fraction',
                coresSeparated=False, branchMissesMeasured=False,
                performanceQualified=False, productionAdmitted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    profile = data_path(root, args.profile)
    output = profile / 'metric-summary.json'
    if output.exists():
        parser.error('fresh summary inside persistent .data recording required')
    receipt = json.loads((profile / 'report.json').read_text())
    if not (receipt['qualified'] and receipt['diagnosticOnly']
            and receipt['targetCompleted'] and receipt['targetExitStatus'] == '0'
            and receipt['binaryUnchanged'] and receipt['gscUnchanged']):
        raise ValueError('completed unchanged retained target required')
    summary = summarize(ET.parse(profile / 'metrics-process.xml').getroot(), receipt['targetPid'])
    summary.update(scope='stdlib-import-process-named-cpu-metrics-not-whole-build',
                   recordingReportSha256=digest(profile / 'report.json'),
                   metricExportSha256=digest(profile / 'metrics-process.xml'),
                   binarySha256=receipt['binarySha256'], targetPid=receipt['targetPid'])
    output.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
