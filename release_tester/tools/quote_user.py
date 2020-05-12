#!/usr/bin/env python
""" quote the user (if enabled) with information about the running frontends """
import logging

def quote_user(cfg):
    """ print all available frontends, and wait for the user to confirm (if) """
    for frontend in cfg.frontends:
        logging.info('frontend can be reached at: ' +
                     '''{f[proto]}://root:{c.passvoid}@{f[ip]}:{f[port]}{path}'''.format(
                        f=frontend,
                        c=cfg,
                        path='/_db/_system/_admin/aardvark/index.html#login'
                      )
                    )
    if cfg.quote_user:
        input("Press Enter to continue")
    else:
        logging.info("Continuing test now.")

def end_test(cfg, which):
    """ print that the test is done, and quote the user to contirue (if) """
    str_which = str(which)
    if cfg.quote_user:
        input("{0} finished - Press Enter to continue.".format(str_which))
    else:
        logging.info("{0} finished - Continuing.".format(str_which))
