#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
from queue import Queue, Empty
from subprocess import PIPE, Popen
import sys
from threading  import Thread
from tools.asciiprint import print_progress as progress
import tools.loghelper as lh

ON_POSIX = 'posix' in sys.builtin_module_names

def dummy_line_result(line):
    """ do nothing with the line... """
    #pylint: disable=W0104
    line

def enqueue_stdout(std_out, queue, instance):
    """ add stdout to the specified queue """
    for line in iter(std_out.readline, b''):
        #print("O: " + str(line))
        queue.put((line, instance))
    #print('0 done!')
    queue.put(-1)
    std_out.close()

def enqueue_stderr(std_err, queue, instance):
    """ add stderr to the specified queue """
    for line in iter(std_err.readline, b''):
        #print("E: " + str(line))
        queue.put((line, instance))
    #print('1 done!')
    queue.put(-1)
    std_err.close()

def convert_result(result_array):
    """ binary -> string """
    result = ""
    for one_line in result_array:
        result += "\n" + one_line[0].decode("utf-8").rstrip()
    return result

def get_type_args(filename):
    """ guess the format by the filename """
    if filename.endswith('jsonl'):
        return ['--type=jsonl']
    if filename.endswith('json'):
        return ['--type=json']
    if filename.endswith('csv'):
        return ['--type=csv']
    raise NotImplementedError("no filename type encoding implemented for " + filename)


class ArangoImportExecutor():
    """ configuration """
    # pylint: disable=W0102
    def __init__(self, config, connect_instance):
        self.connect_instance = connect_instance
        self.cfg = config
        self.read_only = False

    def run_import_monitored(self, args, timeout, verbose=True):
       # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = [
            self.cfg.bin_dir / "arangoimport",
            "--server.endpoint", self.connect_instance.get_endpoint(),
            "--log.level", "debug",
            "--log.foreground-tty", "true",
            "--server.username", str(self.cfg.username),
            "--server.password", str(self.connect_instance.get_passvoid())
        ] + args

        result_line = dummy_line_result
        if verbose:
            lh.log_cmd(run_cmd)
        process = Popen(run_cmd,
                        stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX,
                        cwd=self.cfg.test_data_dir.resolve())
        queue = Queue()
        thread1 = Thread(target=enqueue_stdout, args=(process.stdout,
                                                      queue,
                                                      self.connect_instance))
        thread2 = Thread(target=enqueue_stderr, args=(process.stderr,
                                                      queue,
                                                      self.connect_instance))
        thread1.start()
        thread2.start()

        # ... do other things here
        # out = logfile.open('wb')
        # read line without blocking
        have_timeout = False
        tcount = 0
        close_count = 0
        result = []
        while not have_timeout:
            if not verbose:
                progress("sj" + str(tcount))
            line = ''
            try:
                line = queue.get(timeout=1)
                result_line(line)
            except Empty:
                tcount += 1
                if verbose:
                    progress('T ' + str(tcount))
                have_timeout = tcount >= timeout
            else:
                tcount = 0
                if isinstance(line, tuple):
                    if verbose:
                        print("e: " + str(line[0]))
                    if not str(line[0]).startswith('#'):
                        result.append(line)
                else:
                    close_count += 1
                    if close_count == 2:
                        print(' done!')
                        break
        if have_timeout:
            print(" TIMEOUT OCCURED!")
            process.kill()
        rc_exit = process.wait()
        print(rc_exit)
        thread1.join()
        thread2.join()
        if have_timeout or rc_exit != 0:
            return (False, convert_result(result))
        if len(result) == 0:
            return (True, "")
        return (True, convert_result(result))

    def import_collection(self, collection_name, filename, more_args=[]):
        """ import into any collection """
        args = [
            '--collection', collection_name,
            '--file', filename
        ] + get_type_args(filename) + more_args

        ret = self.run_import_monitored(args,
                                        timeout=20,
                                        verbose=self.cfg.verbose)
        return ret

    def import_smart_edge_collection(self, collection_name, filename, edge_relations, more_args=[]):
        """ import into smart edge collection """
        if len(edge_relations) == 1:
            edge_relations[1] = edge_relations[0]
        args = [
            '--from-collection-prefix', edge_relations[0],
            '--to-collection-prefix', edge_relations[1]
        ] + more_args

        ret = self.import_collection(collection_name,
                                     filename,
                                     more_args=args)
        return ret
