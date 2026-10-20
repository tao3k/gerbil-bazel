"""Optimize only the already-selected fork child's descriptor cleanup."""
from pathlib import Path


GUARD = 'defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)'


def prepare(text):
    anchors = ('#include "c_intf.h"', 'if ((pid = fork ()) < 0)', '            ___closefrom (fd+1);')
    if any(text.count(anchor) != 1 for anchor in anchors):
        raise ValueError('exact original process creation boundaries required')
    helper = Path(__file__).with_name('darwin_fork_fd_probe.h').read_text()
    text = text.replace(anchors[0], anchors[0] + '\n' + helper, 1)
    text = text.replace(anchors[1], '''if ((pid =
#if ''' + GUARD + '''
               gb_fork_with_fd_probe()
#else
               fork ()
#endif
               ) < 0)''', 1)
    text = text.replace(anchors[2], '''#if ''' + GUARD + '''
            if (gb_closefrom_fork_child(fd+1) < 0) goto return_errno;
#else
''' + anchors[2] + '\n#endif', 1)
    return text
