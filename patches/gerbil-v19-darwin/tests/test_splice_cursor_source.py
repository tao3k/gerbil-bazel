from pathlib import Path
import subprocess

from prepare_splice_cursor import PROGRAM


def helper():
    return Path(__file__).with_name('splice_cursor_helper.scm').read_text()


def test_platform_guard_is_darwin_real_gnu_only():
    text = helper().split('#<<splice-cursor-c-end\n')[1].split('\nsplice-cursor-c-end')[0]
    for definitions, expected in (
        (['__APPLE__', '__MACH__', '__GNUC__'], '1'),
        (['__GNUC__'], '0'),
        (['__APPLE__', '__MACH__', '__GNUC__', '__clang__'], '0'),
        (['__APPLE__', '__GNUC__'], '0'),
    ):
        result = subprocess.run(['cpp', '-P', '-undef', *['-D' + item for item in definitions]],
                                input=text, text=True, capture_output=True, check=True)
        assert '___result = ' + expected + ';' in result.stdout


def test_only_zero_suffix_exact_single_wrapper_enters_cursor():
    assert '(eq? ,n 0)' in PROGRAM
    assert '(splice-cursor-exact-wrap? ,stx)' in PROGRAM
    assert '(pair? (##unchecked-structure-ref ,stx 1 splice-cursor-wrap-type' in PROGRAM
    assert '(splice-resume ,stx' in PROGRAM


def test_effect_and_return_boundaries_remain_materialized():
    text = helper()
    assert '(gx#stx-apply-mark (car rest) mark)' in text
    assert '(resume (foldl__0' in text
    assert '(##structure splice-cursor-wrap-type rest #f mark)' in text
    assert '(initial? #t)' in text
    assert '(not (##structure? tail)) (splice-cursor-canonical?)' in text
    assert 'set-cdr!' not in text


def test_native_reader_is_used_and_unsupported_shape_is_rejected():
    assert '(let ((form (read port)))' in PROGRAM
    assert '(write form port)' in PROGRAM
    assert 'exactly one splice definition required' in PROGRAM
    assert 'retained splice lambda shape changed' in PROGRAM
