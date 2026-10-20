"""Generate an isolated native GSC hook fixture; never edit its source input."""
import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-digests', action='store_true')
    parser.add_argument('--planned-producers', action='store_true')
    parser.add_argument('--snapshot-reader', action='store_true')
    parser.add_argument('--closed-link-only', action='store_true')
    parser.add_argument('--member-tools', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    owned = root / '.data'
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_relative_to(owned) or not output.is_relative_to(owned) or output.exists():
        parser.error('owned source and fresh .data output required')
    main_source = (source / 'gsi/main.scm').read_text()
    if args.closed_link_only and not (args.native_digests and args.snapshot_reader):
        parser.error('closed link requires native digests and snapshot reader')
    if args.closed_link_only and args.planned_producers:
        parser.error('closed link must not install the denied singleton producer hooks')
    if args.member_tools and not args.closed_link_only:
        parser.error('member tools require the closed-link native candidate')
    start = main_source.index('                      (define (do-compile-file-to-target ')
    end = main_source.index('                      (define (do-build-executable ', start)
    section = main_source[start:end]
    anchor = '''(compile-file-to-target
                                   file
                                   options: (add-seq-num opts)
                                   output: output)'''
    if section.count(anchor) != 1:
        parser.error('native explicit-output compilation anchor drift')
    if not args.closed_link_only:
        section = section.replace(anchor, anchor.replace('compile-file-to-target', 'generated-c-native-compile-file-to-target', 1))
    main_source = main_source[:start] + section + main_source[end:]
    link_anchor = "    (combine-option! 'pkg-config-path)"
    if main_source.count(link_anchor) != 1:
        parser.error('native linker argument anchor drift')
    if args.closed_link_only:
        option_anchor = '                           (module-ref symbol) (linker-name string)'
        late_anchor = '                      (let loop2 ((lst arguments))'
        if main_source.count(option_anchor) != 1 or main_source.count(late_anchor) != 1:
            parser.error('closed link target/options anchor drift')
        main_source = main_source.replace(option_anchor, option_anchor +
            '\n                           (closed-c-binding string) (closed-c-entry string)', 1)
        late_hook = '''                      (let ((binding (assq 'closed-c-binding options))
                            (entry (assq 'closed-c-entry options))
                            (original-arguments arguments))
                        (set! options (filter (lambda (option)
                                                (not (memq (car option) '(closed-c-binding closed-c-entry)))) options))
                        (set! arguments
                          (generated-c-closed-link-arguments options arguments
                            (c#target-name target) (and binding (cadr binding)) (and entry (cadr entry))))
                        ;; link-flat/incremental default to the last module's
                        ;; directory. Immutable pins must not relocate output.
                        (if (and (not output) (not (equal? arguments original-arguments)))
                            (set! output
                              (path-directory
                                (car (reverse
                                  (generated-c-closed-link-inputs original-arguments)))))))

'''
        main_source = main_source.replace(late_anchor, late_hook + late_anchor, 1)
    else:
        main_source = main_source.replace(link_anchor, link_anchor + '\n\n    (set! arguments (generated-c-native-link-arguments options arguments))')
    if args.planned_producers:
        option_anchor = '                           (module-ref symbol) (linker-name string)'
        if main_source.count(link_anchor) != 1 or main_source.count(option_anchor) != 1:
            parser.error('native producer policy anchor drift')
        main_source = main_source.replace(link_anchor, link_anchor +
            '\n    (set! options (generated-c-native-select-producer-options options))', 1)
        main_source = main_source.replace(option_anchor, option_anchor +
            '\n                           (generated-c-proof)', 1)
    original = (source / 'gsc/_gsc.scm').read_text()
    include_anchor = '(##include "../gsi/main.scm")'
    if original.count(include_anchor) != 1:
        parser.error('native GSC include anchor drift')
    output.mkdir(parents=True)
    (output / 'gsi').mkdir()
    (output / 'gsc').mkdir()
    (output / 'gsi/main.scm').write_text(main_source)
    includes = ('gambit-generated-c-reads.scm', 'gambit-generated-c-closure.scm', 'gambit-generated-c-native.scm')
    if args.closed_link_only:
        includes = ('gambit-generated-c-reads.scm', 'gambit-generated-c-closure.scm',
                    'gambit-generated-c-closed-link.scm')
    if args.native_digests:
        includes += ('gambit-generated-c-native-digest.scm',
                     'gambit-generated-c-native-digest-install.scm')
        shutil.copy2(Path(__file__).parent / 'gambit-file-sha256.c', output / 'gsc/gambit-file-sha256.c')
    if args.planned_producers:
        includes += ('gambit-generated-c-planned-producer.scm',)
    if args.member_tools:
        includes += ('gambit-generated-c-members.scm',)
    for name in includes:
        shutil.copy2(Path(__file__).parent / name, output / 'gsc' / name)
    prelude = '\n'.join(f'(##include "{name}")' for name in includes)
    (output / 'gsc/_gsc.scm').write_text(original.replace(include_anchor, prelude + '\n' + include_anchor))
    if args.snapshot_reader:
        # A separate Git root prevents ignored parent-worktree prefix skipping.
        patch = Path(__file__).parent.parent / '0025-gambit-darwin-generated-c-snapshot-reader.patch'
        subprocess.run(['git', 'init', '-q', str(output)], check=True)
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=output, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=output, check=True)
    if args.member_tools:
        patch = Path(__file__).parent.parent / '0040-gambit-darwin-member-tool-snapshot.patch'
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=output, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=output, check=True)
        # The constructor already installs the locked member helper/include.
        patch = Path(__file__).parent.parent / '0041-gambit-darwin-closed-link-member-proofs.patch'
        selection = '--include=gsc/gambit-generated-c-closed-link.scm'
        subprocess.run(['git', 'apply', '--check', selection, str(patch)], cwd=output, check=True)
        subprocess.run(['git', 'apply', selection, str(patch)], cwd=output, check=True)
        patch = Path(__file__).parent.parent / '0042-gambit-darwin-member-link-request-guard.patch'
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=output, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=output, check=True)


if __name__ == '__main__':
    main()
