#!/usr/bin/python3
from pathlib import Path

import sys
from acquire_packages import acquire_package
from upgrade import run_upgrade
verbose = True
old_version = sys.argv[1] # "3.7.7-nightly"
new_version = sys.argv[2] # "3.8.0-nightly"
download_dir = "/home/package_cache"
test_data_dir = "/home/test_dir"
version_state_dir = Path("/home/versions")
epmagic = '' # not needed for stage 1/2
dlstage = "ftp:stage2"
username = ""
passvoid = ""
if len(sys.argv) > 3:
    dlstage = sys.argv[3]
    username = sys.argv[4]
    passvoid = sys.argv[5]

zip = True

old_version_state = None
new_version_state = None

old_version_content = None
new_version_content = None

for enterprise in [True, False]:
    
    dl_old = acquire_package(old_version, verbose, download_dir, enterprise, epmagic, zip, username, passvoid);
    dl_new = acquire_package(new_version, verbose, download_dir, enterprise, epmagic, zip, username, passvoid);
    
    old_version_state = version_state_dir / Path(dl_old.cfg.version + "_sourceInfo.log")
    new_version_state = version_state_dir / Path(dl_new.cfg.version + "_sourceInfo.log")
    if old_version_state.exists():
        old_version_content = old_version_state.read_text()
    if new_version_state.exists():
        new_version_content = new_version_state.read_text()
    
    fresh_old_content = dl_old.get_version_info(dlstage)
    fresh_new_content = dl_new.get_version_info(dlstage)
    
    if old_version_content == fresh_old_content and new_version_content == fresh_new_content:
        print("we already tested this version. bye.")
        exit(0)
              
    dl_old.get_packages(True, dlstage)
    dl_new.get_packages(True, dlstage)
    
    print("santeuh")
    
    run_upgrade(dl_old.cfg.version,
                dl_new.cfg.version,
                verbose,
                download_dir, test_data_dir,
                enterprise, zip, False,
                "all", False, "127.0.0.1")

old_version_state.write_text(fresh_old_content)
new_version_state.write_text(fresh_new_content)
