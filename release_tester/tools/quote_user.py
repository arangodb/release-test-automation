#!/usr/bin/env python
""" quote the user (if enabled) with information about the running frontends """
import logging

def quote_user(cfg, message="Provide instructions to the user what do. Why must the user wait here?"):
    """ print all available frontends, and wait for the user to confirm (if) """

    #message to give some instruction what to do or test
    if message:
        print("\n\n\n")
        print(message)

    for frontend in cfg.frontends:
        logging.info('\nfrontend can be reached at: ' +
                     '''{f[proto]}://root:{c.passvoid}@{f[ip]}:{f[port]}{path}'''.format(
                         f=frontend,
                         c=cfg,
                         path='/_db/_system/_admin/aardvark/index.html#login'
                     )
                    )
    if cfg.quote_user:
        input("\nPress Enter to continue")
    else:
        print("\nContinuing test now.")

def end_test(cfg, which):
    """ print that the test is done, and quote the user to continue (if) """
    print("\n\n\n{0} sucessfully finished!\n".format(str(which)))
    if cfg.quote_user:
        input("Press Enter to continue.")
    else:
        logging.info("Continuing...")
