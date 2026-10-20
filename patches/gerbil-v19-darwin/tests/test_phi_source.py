from pathlib import Path


def helper():
    return Path(__file__).with_name('phi_source_helper.scm').read_text()


def test_foreign_compiler_forms_are_not_interpreted():
    text = helper()
    for name in ('c-define-type', 'c-declare', 'c-initialize', 'c-lambda', 'c-define'):
        assert name in text
        assert '##' + name in text
    assert 'include-ci' in text
    assert '##inline-host-expression' in text


def test_traversal_is_bounded_and_quoted_data_is_inert():
    text = helper()
    assert '(fuel 131072)' in text
    assert '((<= fuel 0) #f)' in text
    assert "((eq? (car node) 'quote)" in text
    assert '(null? (cddr node))' in text


def test_only_selected_darwin_non_debug_phi_mode_changes():
    text = helper().split('(define (gxc#compile-generated-phi-source', 1)[1]
    for guard in ('phi?', '(gxc#darwin-gnu-source-loader-platform?)',
                  '(gxc#current-compile-static)', '(gxc#current-compile-invoke-gsc)',
                  '(not (gxc#current-compile-debug))', '(gxc#phi-source-code? code)'):
        assert guard in text
    assert text.count('(gxc#compile-scm-file__1 path code phi?)') == 1
    assert '#!gambit-generated-phi-source-v1' in text
    assert '(gxc#remove-loader-native-versions! path)' in text


def test_controls_use_actual_loader_and_real_native_reference():
    text = Path(__file__).with_name('phi_source_controls.scm').read_text()
    assert '__scheme-source' not in text
    assert '(##load source-path' in text
    assert '(load source-path)' in text
    assert '(load-module "source")' in text
    assert '(compile-at native-path gxc#compile-scm-file__1 #f)' in text
    assert '(compile-at debug-path gxc#compile-generated-phi-source #t)' in text
