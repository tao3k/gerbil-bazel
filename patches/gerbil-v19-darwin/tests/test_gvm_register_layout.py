import pytest

from audit_gvm_register_layout import selected_macros, selected_control_transfer


BASE = ('#define __GNUC__ 16\n#define __APPLE__ 1\n'
        '#define ___MAX_LOCAL_GVM_REGS 25\n#define ___R1 ___r1\n')


def test_actual_local_branch():
    assert selected_macros(BASE)['___R1'] == '___r1'


@pytest.mark.parametrize('text', [BASE + '#define __clang__ 1\n',
    BASE.replace('__GNUC__ 16', '__GNUC__ 15'),
    BASE.replace('___R1 ___r1', '___R1 ___PSR1'),
    BASE.replace('___MAX_LOCAL_GVM_REGS 25', '___MAX_LOCAL_GVM_REGS 0')])
def test_wrong_branch_rejected(text):
    with pytest.raises(ValueError):
        selected_macros(text)


CONTROL = BASE + (
    '#define ___USE_TAIL_CALL_TO_EXIT_HOST \n'
    '#define ___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST \n'
    '#define ___TRUST_C_TCO 1\n'
    '#define ___EXIT_HOST() ___TAIL_CALL_VOID(___CALL_LABEL_HOST(___pc,___ps))\n'
    '#define ___TAIL_CALL_VOID(call) ___PROPER_TAIL_CALL(call)\n'
    '#define ___PROPER_TAIL_CALL(call) __attribute__((musttail)) return call\n')


def test_exclusive_proper_tail_branch():
    assert selected_control_transfer(CONTROL)['___TRUST_C_TCO'] == '1'


@pytest.mark.parametrize('text', [
    CONTROL.replace('__attribute__((musttail)) return call', 'return call'),
    CONTROL.replace('#define ___USE_TAIL_CALL_TO_EXIT_HOST \n', ''),
    CONTROL + '#define ___USE_UNWIND_C_STACK_TO_TRAMPOLINE \n',
    CONTROL + '#define __clang__ 1\n',
])
def test_wrong_control_transfer_rejected(text):
    with pytest.raises(ValueError):
        selected_control_transfer(text)
