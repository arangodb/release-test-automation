
from threading import Thread, Lock
from siteconfig import SiteConfig
from tools.socket_counter import get_socket_count

END_THREAD_LOCK = Lock()
END_THREAD = False
OVERLOAD_THREAD = None

def overload_thread(sitecfg, dummy):
    continue_running = True
    while continue_running:
        try:
            sock_count = get_socket_count()
            if sock_count > 8000:
                print(f"Socket count high: {sock_count}")
        except psutil.AccessDenied:
            pass
        psutil.getloadavg()
        if ((load[0] > self.cfg.max_load) or
            (load[1] > self.cfg.max_load1) or
            (load[0] + load_estimate > sitecfg.overload)):
            print(F"{str(load)} <= {load_estimate} Load to high - Disk I/O: " +
                  str(psutil.swap_memory()))
        time.sleep(1)

def spawn_overload_watcher_thread():
    global OVERLOAD_THREAD
    OVERLOAD_THREAD = Thread(target=overload_thread, args=(SiteConfig(''), True))
    OVERLOAD_THREAD.start()

def shutdown_overload_watcher_thread():
    with END_THREAD_LOCK:
        END_THREAD = True
    if OVERLOAD_THREAD is not None:
        OVERLOAD_THREAD.join()

