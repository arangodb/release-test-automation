import functools
import signal
import subprocess
import sys
import time
import traceback


PYTHON = sys.executable
SCRIPT = __file__
ON_WINDOWS = (sys.platform == 'win32')
SIGNALS = {
    signal.SIGINT: 'SIGINT',
    signal.SIGTERM: 'SIGTERM',
}
if ON_WINDOWS:
    SIGNALS[signal.SIGBREAK] = 'SIGBREAK'


def main(name, terminate):
    """If *terminate* is ``True`` (should only be the case if *name* is ``A``),
    A will try to terminate B.

    B and C will always just sleep and wait for things to happen ...

    """
    print('%s started' % name)

    # A and B spawn a subprocess
    if name == 'A':
        child = subproc('B')
    elif name == 'B':
        child = subproc('C')
        child2 = subproc('F')
    else:
        child = None

    # Curry our cleanup func and register it as handler for SIGINT and SIGTERM
    handler = functools.partial(cleanup, name, child)
    signal.signal(signal.SIGINT, handler)
    if ON_WINDOWS:
        signal.signal(signal.SIGBREAK, handler)
    else:
        signal.signal(signal.SIGTERM, handler)

    if terminate:
        # A tries to terminate B
        time.sleep(1)
        print("killing %s"% name)
        term(child)
        print('%s ended' % name)
    else:
        # SIGBREAK cannot interrupt sleep(), so we sleep 10 * 1s instead
        for i in range(10):
            time.sleep(1)
        print('%s done' % name)
        if child:
            child.wait()


def subproc(name):
    """Create and return a new subprocess named *name*."""
    kwargs = {}
    if ON_WINDOWS:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen([PYTHON, SCRIPT, name], **kwargs)
    return proc


def term(proc):
    """Send a SIGTERM/SIGBREAK to *proc* and wait for it to terminate."""
    if ON_WINDOWS:
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        proc.terminate()
    proc.wait()


def cleanup(name, child, signum, frame):
    """Stop the sub=process *child* if *signum* is SIGTERM. Then terminate."""
    try:
        print('%s got a %s' % (name, SIGNALS[signum]))
        if child and (ON_WINDOWS or signum != signal.SIGINT):
            # Forward SIGTERM on Linux or any signal on Windows
            term(child)
    except:
        traceback.print_exc()
    finally:
        sys.exit()


if __name__ == '__main__':
    terminate = False
    if len(sys.argv) == 1:
        name = 'A'
    elif sys.argv[1] == 'term':
        terminate = True
        name = 'A'
    else:
        name = sys.argv[1]  # B or C

    main(name, terminate)
