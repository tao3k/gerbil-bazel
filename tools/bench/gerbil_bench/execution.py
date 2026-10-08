import os
import selectors
import signal
import subprocess
import threading
import time


class Budget:
    def __init__(self, complete, first=None):
        self.started = time.monotonic()
        self.complete, self.first = complete, first
        self.first_elapsed = None
        self.denied = None
        self.lock = threading.Lock()

    def observe(self, qualifies=False):
        with self.lock:
            elapsed = time.monotonic() - self.started
            if self.denied is None:
                if elapsed > self.complete:
                    self.denied = 'complete-time-deadline'
                elif self.first is not None and self.first_elapsed is None and elapsed > self.first:
                    self.denied = 'first-log-deadline'
            if qualifies and self.first_elapsed is None and self.denied is None:
                self.first_elapsed = elapsed
            return self.denied


def execute(command, cwd, env, log, budget, *, compile_only=False, final_ok=False):
    started = time.monotonic()
    budget.observe()
    if budget.denied:
        return dict(passed=False, attempted=False, stop=budget.denied)
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    pending, last, failure, stop = b'', None, False, None
    try:
        with log.open('wb') as output:
            while selector.get_map() or child.poll() is None:
                stop = budget.observe()
                if stop:
                    break
                for key, _ in selector.select(.01):
                    data = os.read(key.fd, 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    output.write(data)
                    output.flush()
                    pending += data
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        line = line.strip()
                        if line:
                            last = line
                            failure |= line.startswith((b'*** ERROR', b'CASE-FAIL', b'MODULE-FAIL',
                                                       b'SUITE-FAIL', b'HARNESS-FAIL'))
                            budget.observe(not compile_only or line.startswith(b'... compile '))
            if pending.strip():
                last = pending.strip()
                failure |= last.startswith((b'*** ERROR', b'CASE-FAIL', b'MODULE-FAIL', b'SUITE-FAIL', b'HARNESS-FAIL'))
                budget.observe(not compile_only or last.startswith(b'... compile '))
            stop = budget.observe() or stop
    finally:
        # Descendants can hold pipes after the root exits; always own the entire group.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
        selector.close()
        child.stdout.close()
    elapsed = time.monotonic() - started
    stop = budget.observe() or stop
    return dict(attempted=True, exitCode=child.returncode, wallSeconds=elapsed,
                stop=stop, passed=not stop and child.returncode == 0 and
                (not final_ok or last == b'OK' and not failure))
