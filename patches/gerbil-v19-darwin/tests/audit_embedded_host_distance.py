"""Bound same-image native host distances; do not infer dynamic call coverage."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from summarize_native_cpu_profile import macho_functions


def control_transfer_sites(disassembly, begin, end):
    if begin % 4 or end % 4 or end <= begin:
        raise ValueError('aligned nonempty native function required')
    instructions = []
    for line in disassembly.splitlines():
        match = re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s', line)
        if match:
            instructions.append((int(match[1], 16), int(match[2], 16)))
    if [pc for pc, _ in instructions] != list(range(begin, end, 4)):
        raise ValueError('complete contiguous function disassembly required')
    sites = []
    for pc, word in instructions:
        opcode = word & 0xfffffc1f
        if opcode in (0xd61f0000, 0xd63f0000):
            sites.append(dict(address=hex(pc), instructionWord=hex(word),
                              kind='br' if opcode == 0xd61f0000 else 'blr',
                              register=(word >> 5) & 31))
    return dict(functionStart=hex(begin), functionEnd=hex(end),
                instructionCount=len(instructions), indirectSites=sites,
                indirectBranchCount=sum(site['kind'] == 'br' for site in sites),
                indirectCallCount=sum(site['kind'] == 'blr' for site in sites),
                authenticatedBranchOpcodesCounted=False,
                dynamicTransferCountMeasured=False, branchMissesMeasured=False,
                performanceQualified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--control-transfer', action='store_true',
                        help='inspect the unchanged common-host instruction extent')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh persistent .data receipt required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    native = macho_functions(binary)
    if native['sha256'] != '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21':
        raise ValueError('retained binary identity mismatch')
    required = ('___H_gerbil____expander____core',
                '___H_gerbil____expander____stx',
                '___H_gerbil____runtime____mop')
    hosts = {name: address for address, names in native['names'].items()
             for name in names if name in required}
    if set(hosts) != set(required):
        raise ValueError('actual function-start symbols required')
    span = native['textEnd'] - native['textStart']
    evidence = dict(scope='same-image-host-distance-not-all-runtime-calls',
                    binarySha256=native['sha256'], uuid=native['uuid'],
                    textSpanBytes=span, hosts=hosts,
                    exceedsFourGiB=span > 4 * 1024**3,
                    commonAslrSlidePreservesDistance=True,
                    dynamicImagesMeasured=False, branchMissesMeasured=False,
                    performanceQualified=False)
    if args.control_transfer:
        common = [pc for pc, names in native['names'].items()
                  if 'gb_coalesced_host' in names]
        if len(common) != 1:
            raise ValueError('unique common host required')
        begin = common[0]
        index = native['starts'].index(begin)
        end = native['starts'][index+1] if index+1 < len(native['starts']) else native['textEnd']
        disassembly = subprocess.check_output([
            'xcrun', 'llvm-objdump', '--disassemble',
            '--start-address=' + hex(begin), '--stop-address=' + hex(end),
            str(binary)], text=True, timeout=30)
        evidence['commonHostControlTransfer'] = control_transfer_sites(disassembly, begin, end)
        if macho_functions(binary)['sha256'] != native['sha256']:
            raise ValueError('binary changed during read-only inspection')
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
