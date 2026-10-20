#!/usr/bin/env python3
"""Generate a guarded C-only keyword-handler outlining prototype."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    baseline, source, output = (p.resolve() for p in (args.baseline, args.source, args.output))
    if not all(p.is_relative_to(repo / ".data") for p in (source, output)):
        parser.error("prototype sources and receipts must remain under .data")
    output.mkdir(parents=True, exist_ok=False)
    home = baseline / "build"
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    scm = baseline / "src/gambit/lib/_kernel.scm"
    expression = ('(import :std/encoding/json) (def found []) '
                  '(def (walk x) (when (pair? x) '
                  '(when (and (eq? (car x) \'##c-code) (pair? (cdr x)) (string? (cadr x))) '
                  '(set! found (cons (cadr x) found))) (walk (car x)) (walk (cdr x)))) '
                  f'(call-with-input-file {json.dumps(str(scm))} '
                  '(lambda (p) (let lp () (let (x (read p)) '
                  '(unless (eof-object? x) (walk x) (lp)))))) '
                  '(displayln (json->string (list->vector (reverse found))))')
    raw = subprocess.check_output([str(home / "bin/gxi"), "-e", expression], env=env, text=True, timeout=30)
    blocks = [code.strip() for code in json.loads(raw.splitlines()[-1])
              if "___SCMOBJ key_vals[___MAX_NB_PARMS];" in code]
    if len(blocks) != 2:
        raise RuntimeError("expected exactly two structured keyword-handler blocks")
    cfile = source / "src/gambit/lib/_kernel.c"
    original = cfile.read_text()
    if original != (baseline / "src/gambit/lib/_kernel.c").read_text():
        raise RuntimeError("prototype requires unchanged original generated C")
    guard = "defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && (___NB_GVM_REGS == 5)"
    fields = ["HEAP", "FP", "R0", "R1", "R2", "R3", "R4"]
    declarations = " ".join("___D_" + name for name in fields)
    reads = " ".join("___R_" + name for name in fields)
    writes = " ".join("___W_" + name for name in fields)
    helpers = [f"#if {guard}", f"#define ___DARWIN_KEY_READ {reads}",
               f"#define ___DARWIN_KEY_WRITE {writes}",
               "#define ___DARWIN_KEY_JUMP(nargs,val) do { nargs; ___pc=(val); goto ___darwin_keyword_done; } while (0);"]
    patched = original
    for index, body in enumerate(blocks):
        name = f"___darwin_keyword_handler_{index}"
        if patched.count(body) != 1:
            raise RuntimeError("structured C fragment must match generated input exactly once")
        outlined = body.replace("___W_ALL", "___DARWIN_KEY_WRITE").replace("___R_ALL", "___DARWIN_KEY_READ")
        outlined = outlined.replace("___JUMPEXTPRM", "___DARWIN_KEY_JUMP").replace("___JUMPPRM", "___DARWIN_KEY_JUMP")
        helpers += [f"static __attribute__((noinline)) void {name} (___processor_state ___ps) {{",
                    "___WORD ___pc, ___temp;", declarations, "___DARWIN_KEY_READ", outlined,
                    "___darwin_keyword_done:", "___ps->pc=___pc;", "___DARWIN_KEY_WRITE", "}"]
        replacement = (f"#if {guard}\n___W_ALL\n{name} (___ps);\n___R_ALL\n"
                       "___JUMPEXT(___ps->pc)\n#else\n" + body + "\n#endif")
        patched = patched.replace(body, replacement, 1)
    helpers += ["#undef ___DARWIN_KEY_JUMP", "#undef ___DARWIN_KEY_WRITE", "#undef ___DARWIN_KEY_READ", "#endif"]
    marker = "#undef ___MD_ALL\n"
    if patched.count(marker) != 1:
        raise RuntimeError("generated module declaration boundary must be unique")
    patched = patched.replace(marker, "\n".join(helpers) + "\n\n" + marker, 1)
    cfile.write_text(patched)
    report = {"prototypeOnly": True, "performanceQualified": False,
              "guard": guard, "outlinedHandlerCount": len(blocks),
              "originalCSha256": hashlib.sha256(original.encode()).hexdigest(),
              "candidateCSha256": hashlib.sha256(patched.encode()).hexdigest(),
              "schemeSourceUnchanged": True, "registerAbiChanged": False}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
