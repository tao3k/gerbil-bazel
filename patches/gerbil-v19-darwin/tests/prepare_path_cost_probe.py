"""Observe native path costs without changing filesystem policy or consumers."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess


SPECS = {
    'os_files.c': [
        ('char *', 'getcwd_long_path', 'char *buf, ___SIZE_T size', 'buf,size', 0, 'USE_getcwd'),
        ('___SCMOBJ ', '___os_path_normalize_directory', '___SCMOBJ path', 'path', 1, None),
    ],
    'os_setup.c': [
        ('___SCMOBJ ', '___os_file_info', '___SCMOBJ fi, ___SCMOBJ path, ___SCMOBJ chase',
         'fi,path,chase', 2, None),
    ],
}


def instrument(source, unit):
    anchor = '#include "setup.h"\n'
    if source.count(anchor) != 1:
        raise ValueError('original native include anchor changed')
    source = source.replace(anchor, anchor + f'#define GB_PATH_UNIT "{unit}"\n'
                            '#include "gambit-path-cost-probe.h"\n')
    for result_type, name, arguments, call, slot, guard in SPECS[unit + '.c']:
        definition = result_type + name + '\n'
        if source.count(definition) != 1:
            raise ValueError('original native function definition changed: ' + name)
        original = 'gb_path_original_' + name
        source = source.replace(definition, 'static ' + result_type + original + '\n')
        wrapper = f'''\n{result_type}{name}({arguments}) {{
  struct gb_path_stamp stamp;
  gb_path_begin(&stamp);
  {result_type}result={original}({call});
  int saved=errno;
  gb_path_finish(&stamp,{slot});
  errno=saved;
  return result;
}}
'''
        source += f'\n#ifdef {guard}\n{wrapper}\n#endif\n' if guard else wrapper
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3] / '.data'
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if platform.system() != 'Darwin' or output.exists() or not all(
            path.is_relative_to(root) for path in (baseline, output)):
        parser.error('fresh isolated Darwin project-data source required')
    subprocess.run(['/bin/cp', '-cR', str(baseline), str(output)], check=True)
    header = Path(__file__).with_name('gambit-path-cost-probe.h')
    directory = output / 'src/gambit/lib'
    hashes = {}
    for filename in SPECS:
        path = directory / filename
        source = path.read_text()
        changed = instrument(source, path.stem)
        path.write_text(changed)
        hashes[filename] = {'original': hashlib.sha256(source.encode()).hexdigest(),
                            'diagnostic': hashlib.sha256(changed.encode()).hexdigest()}
    (directory / header.name).write_bytes(header.read_bytes())
    report = {'scope': 'native-path-cost-diagnostic-not-performance', 'sourceHashes': hashes,
              'headerSha256': hashlib.sha256(header.read_bytes()).hexdigest(),
              'filesystemPolicyChanged': False, 'consumerFlagsChanged': False,
              'nestedCostsMustNotBeSummed': True}
    (output / 'path-cost-probe-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PATH-COST-PREPARED observation only; filesystem policy unchanged', flush=True)


if __name__ == '__main__':
    main()
