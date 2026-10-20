from pathlib import Path
import subprocess

from run_fd_executable_link_progressive import render_wrapper


def execute(tmp_path, arguments):
    compiler = tmp_path / 'GNU compiler'
    compiler.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    compiler.chmod(0o755)
    wrapper = tmp_path / 'wrapper'
    obj = tmp_path / 'runtime object.o'
    log = tmp_path / 'links.log'
    wrapper.write_text(render_wrapper(compiler, obj, log))
    result = subprocess.check_output(['/bin/sh', str(wrapper), *arguments], text=True).splitlines()
    return result, obj, log


def test_final_object_precedes_archive_and_flags_stay_exact(tmp_path):
    args = ['-w', '-o', 'server', 'server.o', '-L', 'original/lib', '-lgambit', '-ldl']
    result, obj, log = execute(tmp_path, args)
    assert result == [str(obj), *args]
    assert log.read_text().splitlines() == ['LINK', *args]


def test_compile_and_preprocessor_invocations_are_untouched(tmp_path):
    args = ['-c', 'module.c', '-o', 'module.o', '-lgambit']
    result, _, log = execute(tmp_path, args)
    assert result == args
    assert not log.exists()


def test_other_links_do_not_receive_runtime_object(tmp_path):
    args = ['-o', 'foreign', 'foreign.o', '-lm']
    result, _, log = execute(tmp_path, args)
    assert result == args
    assert not log.exists()
