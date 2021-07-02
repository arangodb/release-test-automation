#!/usr/bin/env python
import platform
import signal
import subprocess
import time

winver = platform.win32_ver()
if winver[0]:
    WINDOWS = True
    POSIX = False
    # may throw on elderly wintendos?
    from psutil import Process, Popen
    from psutil import _psutil_windows as cext

    from psutil._pswindows import WindowsService

    class WindowsService_monkey(WindowsService):
        # actions
        # XXX: the necessary C bindings for start() and stop() are
        # implemented but for now I prefer not to expose them.
        # I may change my mind in the future. Reasons:
        # - they require Administrator privileges
        # - can't implement a timeout for stop() (unless by using a thread,
        #   which sucks)
        # - would require adding ServiceAlreadyStarted and
        #   ServiceAlreadyStopped exceptions, adding two new APIs.
        # - we might also want to have modify(), which would basically mean
        #   rewriting win32serviceutil.ChangeServiceConfig, which involves a
        #   lot of stuff (and API constants which would pollute the API), see:
        #   http://pyxr.sourceforge.net/PyXR/c/python24/lib/site-packages/
        #       win32/lib/win32serviceutil.py.html#0175
        # - psutil is typically about "read only" monitoring stuff;
        #   win_service_* APIs should only be used to retrieve a service and
        #   check whether it's running

        def start(self, timeout=None):
            with self._wrap_exceptions():
                cext.winservice_start(self.name())
                if timeout:
                    giveup_at = time.time() + timeout
                    while True:
                        if self.status() == "running":
                            return
                        else:
                            if time.time() > giveup_at:
                                raise TimeoutExpired(timeout)
                            else:
                                time.sleep(.1)

        def stop(self):
            # Note: timeout is not implemented because it's just not
            # possible, see:
            # http://stackoverflow.com/questions/11973228/
            with self._wrap_exceptions():
                return cext.winservice_stop(self.name())

    WindowsService.start = WindowsService_monkey.start
    WindowsService.stop = WindowsService_monkey.stop


    class Process_monkey(Process):
        """ overload this function """
        def terminate(self):
            """Terminate the process with SIGTERM pre-emptively checking
            whether PID has been reused.
            On Windows this will only work for processes spawned through psutil
            or started using
               kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP.
            """
            if POSIX:
                self._send_signal(signal.SIGTERM)
            else:  # pragma: no cover
                def sigint_boomerang_handler(signum, frame):
                    if signum != signal.SIGINT:
                        exit(1)
                    pass
                original_sigint_handler = signal.getsignal(signal.SIGINT)
                signal.signal(signal.SIGINT, sigint_boomerang_handler)
                self.send_signal(signal.CTRL_BREAK_EVENT)
                self.wait()
                # restore original handler
                signal.signal(signal.SIGINT, original_sigint_handler)

    Process.terminate = Process_monkey.terminate

    class Popen_monkey(Popen):
        """ overload this function """
        def __init__(self, *args, **kwargs):
            # Explicitly avoid to raise NoSuchProcess in case the process
            # spawned by subprocess.Popen terminates too quickly, see:
            # https://github.com/giampaolo/psutil/issues/193
            print("santoehusanotehusanoethsnaoteuh")
            if WINDOWS:
                kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            self.__subproc = subprocess.Popen(*args, **kwargs)
            self._init(self.__subproc.pid, _ignore_nsp=True)

    print(dir(Popen_monkey))
    print(dir(Popen))
    Popen.__init__ = Popen_monkey.__init__
