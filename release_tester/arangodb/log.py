#!/usr/bin/env python
""" analyse the logfile of a running arangod instance
    for certain status messages """

import sys, os
import re
import time
import logging

class ArangodLogExaminer():
    """ examine the logfiles of all arangods attached to one starter"""
    def __init__(self, config):
        self.cfg = config
        self.is_master = False
        self.is_leader = False
        self.frontend_port = 8529

    def detect_instance_pids(self):
        #TODO I am not sure if this is the most robust way to detect
        #if a server is running. I guess I might be a solution that
        #is better portable than others.
        #if all OSs would provide a `netstat -nlp` like functionality
        #you could try to go with a api version once you expect the
        #server to be up. On the otherhand maybe we want to test
        #for collection loss in the future.
        """ try to detect the PID of the current instances
            and check that they ready for business"""
        for i in self.cfg.all_instances:
            instance = self.cfg.all_instances[i]
            instance['PID'] = 0

            ## TODO what is the pid is never found - should we loop forever?
            ## 20 tries ok
            tries = 20
            while instance['PID'] == 0 and tries:

                log_file_content = ''
                last_line = ''

                with open(instance['logfile']) as log_fh:
                    for line in log_fh:
                        # skip empty lines
                        if line == "":
                            continue
                        # save last line and append to string (why not slurp the whole file?)
                        last_line = line
                        log_file_content += '\n' + line

                #check last line or continue
                match = re.search(r'Z \[(\d*)\]', last_line)
                if match is None:
                    logging.info("no PID in: %s", last_line)
                    continue

                # pid found now find the position of the pid in
                # the logfile and check it is followed by a
                # ready for business.
                pid = match.groups()[0]
                start = log_file_content.find(pid)
                pos = log_file_content.find('is ready for business.', start)
                if pos < 0:
                    print('.', end='')
                    sys.stdout.flush()
                    time.sleep(1)
                    continue
                instance['PID'] = int(pid)

            if instance['PID'] == 0:
                print()
                logging.error("could not get pid for instance: " + str(instance))
                logging.error("inspect: " + str(instance['logfile']))
                sys.exit(1)
            else:
                logging.info("found pid {0} for instance with logifle {1}.".format(instance['PID'], instance['logfile']))
        print()
