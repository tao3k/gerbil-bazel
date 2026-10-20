"""Attribute inclusive loader stacks; overlapping cycle categories are not additive."""
import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def attribute(root):
    ids = {node.get('id'): node for node in root.iter() if node.get('id')}

    def resolve(node):
        return ids[node.get('ref')] if node.get('ref') else node

    groups, images, callers = Counter(), Counter(), Counter()
    total = samples = 0
    for row in root.iter('row'):
        fields = list(row)
        if resolve(fields[4]).text != 'Running':
            continue
        weight = int(resolve(fields[5]).text)
        if weight < 0:
            raise ValueError('negative active cycles')
        total += weight
        samples += 1
        backtrace = resolve(fields[6]).find('backtrace')
        if backtrace is None:
            continue
        frames = [resolve(frame) for frame in resolve(backtrace)]
        if not frames:
            continue
        names = [frame.get('name', '') for frame in frames]
        binary = frames[0].find('binary')
        path = resolve(binary).get('path', '') if binary is not None else ''
        images[path] += weight
        dlopen = any('dyld4::APIs::dlopen_from(' in name for name in names)
        atlas = any('ExternallyViewableState::generateAtlas(' in name for name in names)
        if dlopen:
            groups['dlopen-stack-inclusive'] += weight
            for name in set(names):
                if 'load' in name.lower() and not name.startswith('dyld'):
                    callers[name] += weight
        if any('dyld4::APIs::dlsym_from(' in name for name in names):
            groups['dlsym-stack-inclusive'] += weight
        if atlas:
            groups['atlas-stack-inclusive'] += weight
        if atlas and dlopen:
            groups['atlas-inside-dlopen-inclusive'] += weight
        if path in ('/usr/lib/dyld', '/usr/lib/system/libdyld.dylib'):
            groups['dyld-image-self'] += weight
    if total <= 0:
        raise ValueError('no positive Running active cycles')

    def rows(counter):
        return [dict(name=name, cycles=count, percent=100*count/total)
                for name, count in counter.most_common()]

    return dict(scope='sampled-native-prefix-stack-attribution-not-speedup',
                totalCycles=total, runningSamples=samples, overlappingCategories=True,
                groups=rows(groups), images=rows(images), loaderCallers=rows(callers))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads((args.profile / 'report.json').read_text())
    if receipt.get('qualified') is not True or receipt.get('performanceQualified') is not False:
        parser.error('qualified diagnostic CPU profile required')
    report = attribute(ET.parse(args.profile / 'cpu-profile.xml').getroot())
    report['profileScope'] = receipt['scope']
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('totalCycles', 'runningSamples', 'groups')}, indent=2))


if __name__ == '__main__':
    main()
