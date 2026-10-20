"""Offline physical-table validation and fixed-order hash distribution models."""
import argparse
import json
from pathlib import Path

from experiment_framework.context import data_path, FROZEN_47_SHA256
from native_object_manifest import digest

UNUSED = (1 << 63) - 52
MASK32 = (1 << 32) - 1
MASK64 = (1 << 64) - 1


def parse_tables(text):
    tables = {}
    for line in text.splitlines():
        fields = line.split('\t')
        if fields[0] == 'STDLIB-HASH-TABLE':
            if len(fields) != 5:
                raise ValueError('complete table header required')
            index, size, flags, count = map(int, fields[1:])
            if index in tables or size < 7 or (size - 5) % 2 or flags & 4:
                raise ValueError('unique normalized physical table required')
            tables[index] = dict(size=size, count=count, slots=[])
        elif fields[0] == 'STDLIB-HASH-SLOT':
            if len(fields) != 4:
                raise ValueError('complete slot required')
            index, slot, encoding = map(int, fields[1:])
            if index not in tables or slot != len(tables[index]['slots']):
                raise ValueError('ordered declared slots required')
            if encoding != UNUSED and not (0 <= encoding < 1 << 63 and encoding % 4 == 1):
                raise ValueError('subtype-one key or UNUSED required')
            tables[index]['slots'].append(encoding)
    if (not tables or text.splitlines().count('STDLIB-HASH-LAYOUT-OK') != 1
            or text.splitlines()[-2:] != ['CONTEXT-IDENTITY-OK', 'OK']):
        raise ValueError('complete original snapshot required')
    for table in tables.values():
        slots = table['slots']
        keys = [key for key in slots if key != UNUSED]
        if (len(slots) * 2 + 5 != table['size'] or len(keys) != table['count']
                or len(set(keys)) != len(keys) or len(keys) >= len(slots)):
            raise ValueError('exact count, unique keys and terminating empty slot required')
    return [table['slots'] for table in tables.values()]


def mixed_key(encoding, model):
    raw = (2 * encoding - 1) & MASK64
    rotated = ((raw >> 3) | (raw << 61)) & MASK64
    value = (rotated ^ (rotated >> 32)) & MASK32
    if model == 'original':
        rotation = ((value << 16) | (value >> 16)) & MASK32
        return (value ^ (4353 * rotation)) & MASK32
    if model != 'avalanche32':
        raise ValueError('known offline mixer required')
    value ^= value >> 16
    value = value * 0x85EBCA6B & MASK32
    value ^= value >> 13
    value = value * 0xC2B2AE35 & MASK32
    return value ^ (value >> 16)


def physical_probes(tables):
    lengths = []
    for slots in tables:
        capacity = len(slots)
        for index, key in enumerate(slots):
            if key == UNUSED:
                continue
            home = mixed_key(key, 'original') * capacity >> 32
            distance = (home - index) % capacity
            if any(slots[(home - step) % capacity] == UNUSED for step in range(distance)):
                raise ValueError('key unreachable under original address hash')
            lengths.append(distance + 1)
    if not lengths:
        raise ValueError('occupied original keys required')
    return dict(keys=len(lengths), successfulMean=sum(lengths) / len(lengths),
                successfulMaximum=max(lengths))


def replay(tables, model):
    lengths, missing, capacity_sum = [], 0, 0
    for slots in tables:
        capacity = len(slots)
        placed = [None] * capacity
        for key in slots:
            if key == UNUSED:
                continue
            position = mixed_key(key, model) * capacity >> 32
            length = 1
            while placed[position] is not None:
                position = (position - 1) % capacity
                length += 1
            placed[position] = key
            lengths.append(length)
        for home in range(capacity):
            position, length = home, 1
            while placed[position] is not None:
                position = (position - 1) % capacity
                length += 1
            missing += length
        capacity_sum += capacity
    return dict(model=model, keys=len(lengths), successfulMean=sum(lengths) / len(lengths),
                insertionMaximum=max(lengths), uniformMissingMean=missing / capacity_sum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    snapshot = data_path(root, args.snapshot)
    output = data_path(root, args.output, fresh=True)
    source = json.loads((snapshot / 'report.json').read_text())
    if (source.get('qualified') is not True or source.get('hashLayoutDiagnostic') is not True
            or source.get('binarySha256') != FROZEN_47_SHA256
            or source.get('binaryUnchanged') is not True or len(source.get('runs', [])) != 1
            or source['runs'][0].get('exitCode') != 0):
        raise ValueError('completed frozen-runtime physical snapshot required')
    log = snapshot / '0.log'
    tables = parse_tables(log.read_text())
    report = dict(scope='offline-physical-table-and-fixed-slot-order-model-not-executed-candidate',
                  diagnosticOnly=True, performanceQualified=False, productionAdmitted=False,
                  snapshotReportSha256=digest(snapshot / 'report.json'), logSha256=digest(log),
                  tables=len(tables), physical=physical_probes(tables),
                  models=[replay(tables, model) for model in ('original', 'avalanche32')])
    output.mkdir()
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return 0
