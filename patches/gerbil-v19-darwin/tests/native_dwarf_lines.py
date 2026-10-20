"""Decode LLVM's DWARF line-table intervals, with explicit sequence boundaries."""
import bisect
import json
import re


def line_intervals(dump):
    if len(re.findall(r'^debug_line\[', dump, re.MULTILINE)) != 1:
        raise ValueError('one qualified compilation-unit line table required')
    expected = 'Address            Line   Column File   ISA Discriminator OpIndex Flags'
    if expected not in dump.splitlines():
        raise ValueError('LLVM DWARF line-column schema changed')
    directories, names, files, ranges = {}, {}, {}, []
    current_file = previous = None
    for line in dump.splitlines():
        directory = re.fullmatch(r'include_directories\[\s*(\d+)\] = (".*")', line)
        if directory:
            directories[int(directory[1])] = json.loads(directory[2])
        file = re.fullmatch(r'file_names\[\s*(\d+)\]:', line)
        if file:
            current_file = int(file[1])
        name = re.fullmatch(r'\s+name: (".*")', line)
        if name and current_file is not None:
            names[current_file] = json.loads(name[1])
        directory_index = re.fullmatch(r'\s+dir_index: (\d+)', line)
        if directory_index and current_file is not None:
            index = int(directory_index[1])
            if index not in directories or current_file not in names:
                raise ValueError('DWARF file metadata is incomplete')
            files[current_file] = (directories[index], names[current_file])
        if not line.startswith('0x'):
            continue
        fields = line.split()
        if len(fields) < 7:
            raise ValueError('incomplete DWARF address row')
        address = int(fields[0], 16)
        number, column, file_index, isa, discriminator, op_index = map(int, fields[1:7])
        if isa or op_index or number < 0 or column < 0 or discriminator < 0:
            raise ValueError('unsupported DWARF instruction row')
        if previous:
            start, old_line, old_file = previous
            if address < start:
                raise ValueError('DWARF sequence address moved backward')
            if address > start and old_line:
                if old_file not in files:
                    raise ValueError('unknown DWARF source file')
                ranges.append((start, address, old_file, old_line))
        previous = None if 'end_sequence' in fields[7:] else (address, number, file_index)
    if previous is not None:
        raise ValueError('unterminated DWARF line sequence')
    ranges.sort()
    if not ranges or any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
        raise ValueError('empty or overlapping DWARF line intervals')
    return ranges, files


def lookup_line(ranges, starts, address):
    index = bisect.bisect_right(starts, address)-1
    if index < 0 or address >= ranges[index][1]:
        return None
    return ranges[index][2:]
