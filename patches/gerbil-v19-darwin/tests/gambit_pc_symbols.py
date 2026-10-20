"""Diagnostic native PC landmarks; not a performance transformation."""
import re


def inject(text, start_index=0):
    rows = []
    result = []
    procedure = None
    module = None
    guard = ("defined(__APPLE__) && defined(__GNUC__) && "
             "!defined(__clang__)")
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        module_match = re.match(r'#define ___MODULE_NAME "([^"]+)"', line)
        if module_match:
            module = module_match[1]
        match = re.match(r"#define ___PH_PROC (\w+)\s*$", line)
        if match:
            procedure = match[1]
        result.append(line)
        match = re.match(r"___DEF_(?:G|S)LBL\((?:\d+,)?(\w+)\)\s*$", line)
        if match:
            index = start_index + len(rows)
            rows.append({"index": index, "label": match[1],
                         "procedure": procedure, "module": module, "originalLine": number})
            # GCC's unique asm suffix also supports compiler-created block copies.
            result.append(f'#if {guard}\n'
                          f'__asm__ __volatile__(".globl _gb_vm_pc_{index}_%=\\n'
                          f'_gb_vm_pc_{index}_%=:\\n" : : );\n#endif\n')
    if not rows:
        raise ValueError("no original GVM label landmarks")
    return "".join(result), rows
