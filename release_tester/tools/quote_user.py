#!/usr/bin/env python
""" quote the user (if enabled) with information about the running frontends """
import logging

def quote_user(cfg):
    """ print all available frontends, and wait for the user to confirm (if) """
    for frontend in cfg.frontends:
        print(frontend)
        logging.info('frontend can be reached at: '
                     '%s://root:%s@%s:%s%s',
                     frontend['proto'],
                     cfg.passvoid,
                     frontend['ip'],
                     frontend['port'],
                     '/_db/_system/_admin/aardvark/index.html#login')
    if cfg.quote_user:
        input("Press Enter to continue")
    else:
        logging.info("Continuing test now.")

def end_test(cfg, which):
    """ print that the test is done, and quote the user to contirue (if) """
    if cfg.quote_user:
        input(str(which) + " finished - Press Enter to continue")
    else:
        logging.info("%s finished. continuing.", str(which))
