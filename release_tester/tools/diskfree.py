#!/usr/bin/env python3
""" helpers to ensure enough disk is available for the test """

import shutil
import time

def check_diskfree(testdir, disk_used):
    """ check whether testdir has more than disk_used space available """
    count = 1
    while True:
        try:
            diskfree = shutil.disk_usage(str(testdir))
            break
        except FileNotFoundError:
            count += 1
            if count > 20:
                break
            testdir.mkdir()
            time.sleep(1)
            print(".")

    if count > 20:
        raise TimeoutError("disk_usage on " + str(testdir) + " not working")

    df_mb = diskfree.free / (1024 * 1024)
    if df_mb > diskfree.free:
        print(
            f"Scenario demanded {disk_used} MB but only {df_mb} MB are available in {str(testdir)}"
        )
        raise Exception("not enough free disk space to execute test!")
