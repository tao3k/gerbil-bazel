"""Correlate time-sample leaves with metric buckets, not instruction attribution."""
import argparse
import bisect
from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from native_object_manifest import digest
from summarize_native_cpu_profile import classify_native_pc, macho_functions
from summarize_stdlib_counter_profile import CATEGORIES, precise_metric_groups, summarize
from experiment_framework.xml_evidence import XmlTable
from experiment_framework.context import data_path


def layout_geometry(native, sites, page_size):
    if type(page_size) is not int or page_size < 4 or page_size & (page_size - 1):
        raise ValueError('actual power-of-two page size required')
    if not sites:
        raise ValueError('validated native sample sites required')
    functions = defaultdict(Counter)
    for (begin, pc), weight in sites.items():
        if pc % 4 or pc < begin or weight < 0:
            raise ValueError('aligned validated native site required')
        functions[begin][pc] += weight
    rows = []
    for begin, points in functions.items():
        index = bisect.bisect_left(native['starts'], begin)
        if index == len(native['starts']) or native['starts'][index] != begin:
            raise ValueError('actual native function start required')
        end = native['starts'][index + 1] if index + 1 < len(native['starts']) else native['textEnd']
        if max(points) >= end:
            raise ValueError('sample must stay within actual function extent')
        offsets = [pc - begin for pc in points]
        current = len({pc // page_size for pc in points})
        best = min(len({(offset + shift) // page_size for offset in offsets})
                   for shift in range(0, page_size, 4))
        rows.append(dict(functionStart=hex(begin), names=sorted(native['names'].get(begin, [])),
                         functionExtentBytes=end-begin, distinctSampledPCs=len(points),
                         sampleWeightNanoseconds=sum(points.values()),
                         observedSampledPages=current,
                         unconstrainedTranslationLowerBoundPages=best,
                         maximumWithinFunctionSampledPageReduction=current-best))
    return dict(pageSize=page_size, functions=sorted(rows,
                key=lambda row: row['sampleWeightNanoseconds'], reverse=True),
                totalObservedNativeSampledPages=len({pc // page_size for _, pc in sites}),
                scope='sampled-native-page-geometry-not-page-fault-or-instruction-cost',
                translationIsNotALinkerRecipe=True, functionEntryOrderRecorded=False,
                pageFaultAttribution=False, instructionAttribution=False,
                performanceQualified=False)


def correlate(tree, pid, native, groups, *, include_context=False, page_size=None, include_sites=False):
    table = XmlTable(tree, ['time', 'thread', 'process', 'core', 'thread-state', 'weight', 'stack'])
    resolve = table.resolve
    intervals = sorted(groups)
    starts = [start for start, _ in intervals]
    counts, weights, kinds = Counter(), Counter(), Counter()
    metrics = defaultdict(Counter)
    skipped = Counter()
    sites = Counter()
    contexts = defaultdict(lambda: dict(samples=0, sampleWeightNanoseconds=0,
                                       stackDepthSamples=Counter(),
                                       bucketMetricProxyNanoseconds=Counter()))
    for fields in table.rows():
        if int(resolve(fields[2].find('pid')).text) != pid:
            raise ValueError('exact target time sample required')
        if fields[4].text != 'Running':
            skipped['notRunning'] += 1
            continue
        timestamp, weight = int(fields[0].text), int(fields[5].text)
        if timestamp < 0 or weight < 0:
            raise ValueError('invalid time sample')
        index = bisect.bisect_right(starts, timestamp) - 1
        if index < 0 or timestamp >= sum(intervals[index]):
            skipped['outsidePreciseBucket'] += 1
            continue
        group = groups[intervals[index]]
        mass = math.fsum(group[name] for name in CATEGORIES)
        if mass <= 0:
            skipped['emptyMetricMass'] += 1
            continue
        stack = fields[6].find('backtrace')
        if stack is None:
            skipped['noBacktrace'] += 1
            continue
        frames = list(resolve(stack))
        if not frames:
            skipped['noLeaf'] += 1
            continue
        leaf = resolve(frames[0])
        image = leaf.find('binary')
        if image is None:
            name, kind = 'UNKNOWN_IMAGE', 'unknown'
        else:
            image = resolve(image)
            if image.get('UUID') == native['uuid']:
                if (page_size is not None and
                        (int(image.get('load-addr'), 16) - native['textBase']) % page_size):
                    raise ValueError('actual image page alignment required')
                pc = int(leaf.get('addr'), 16) - int(image.get('load-addr'), 16) + native['textBase']
                name, kind = classify_native_pc(native, pc, leaf.get('name'))
                if (page_size is not None or include_sites) and kind == 'validatedNativeCycles':
                    aligned = pc & ~3
                    index = bisect.bisect_right(native['starts'], aligned) - 1
                    begin = native['starts'][index]
                    sites[begin, aligned] += weight
            else:
                if image.get('name') in ('gerbil', 'gxi'):
                    raise ValueError('unexpected runtime image UUID')
                name, kind = f"EXTERNAL:{image.get('name')}:{leaf.get('name')}", 'external'
        counts[name] += 1
        weights[name] += weight
        kinds[kind] += 1
        for category in CATEGORIES:
            metrics[name][category] += weight * group[category] / mass
        if include_context:
            core = resolve(fields[3])
            label = core.get('fmt', '')
            match = re.fullmatch(r'CPU (\d+) \(([PE]) Core\)', label)
            if match is None or int(match[1]) != int(core.text):
                raise ValueError('explicit matching P/E core identity required')
            context = contexts[match[2]]
            context['samples'] += 1
            context['sampleWeightNanoseconds'] += weight
            context['stackDepthSamples'][str(len(frames))] += 1
            for category in CATEGORIES:
                context['bucketMetricProxyNanoseconds'][category] += weight * group[category] / mass
    if not counts:
        raise ValueError('no matched running target samples')
    result = dict(matchedRunningSamples=sum(counts.values()), skipped=dict(skipped),
                leafValidation=dict(kinds), sampleWeightNanoseconds=sum(weights.values()),
                topLeaves=[dict(name=name, samples=counts[name], sampleWeightNanoseconds=weight,
                                bucketMetricProxyNanoseconds=dict(metrics[name]))
                           for name, weight in weights.most_common(20)],
                instructionAttribution=False, exclusiveProcedureCost=False,
                scope='time-sample-leaf-and-bucket-correlation-not-hardware-cycle-attribution',
                performanceQualified=False, productionAdmitted=False)
    if include_context:
        result.update(coreContext=dict(contexts),
                      coreMetricsAreProcessBucketProxies=True,
                      coreCycleAttribution=False, schedulerCauseEstablished=False)
    if include_sites:
        result['nativeSites'] = [dict(functionStart=hex(begin), nativePc=hex(pc),
                                     sampleWeightNanoseconds=weight)
                                for (begin, pc), weight in sites.most_common()]
    if page_size is not None:
        result['nativePageGeometry'] = layout_geometry(native, sites, page_size)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='fresh private correlation output')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--context', action='store_true',
                        help='write separate P/E core and stack-depth coverage evidence')
    mode.add_argument('--layout', action='store_true',
                      help='audit existing sampled Mach-O page geometry without rerunning the target')
    mode.add_argument('--native-sites', action='store_true',
                      help='export validated native PCs for exact debug-sidecar lookup, not GVM proximity')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    profile = data_path(root, args.profile)
    output = profile / ('stack-native-sites.json' if args.native_sites else 'stack-layout.json' if args.layout else
                        'stack-context.json' if args.context else 'stack-correlation.json')
    if args.output:
        output = data_path(root, args.output, fresh=True)
    if output.exists():
        parser.error('fresh persistent .data correlation required')
    receipt = json.loads((profile / 'report.json').read_text())
    if not (receipt['qualified'] and receipt['targetCompleted'] and receipt['diagnosticOnly']):
        raise ValueError('completed diagnostic target required')
    native = macho_functions(root / '.data/d1510-reader-whitespace-native-v2/gerbil')
    if native['sha256'] != receipt['binarySha256']:
        raise ValueError('runtime identity changed')
    tree = ET.parse(profile / 'metrics-process.xml').getroot()
    summarize(tree, receipt['targetPid'])
    groups, _ = precise_metric_groups(tree, receipt['targetPid'])
    result = correlate(ET.parse(profile / 'time-profile.xml').getroot(),
                       receipt['targetPid'], native, groups, include_context=args.context,
                       page_size=os.sysconf('SC_PAGE_SIZE') if args.layout else None,
                       include_sites=args.native_sites)
    result.update(binarySha256=native['sha256'],
                  timeExportSha256=digest(profile / 'time-profile.xml'),
                  metricExportSha256=digest(profile / 'metrics-process.xml'))
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
